import abc
import importlib
import inspect
import json
import warnings
from abc import ABCMeta

from loguru import logger

from pymemri import PodClient
from pymemri.data.basic import read_json
from pymemri.webserver.public_api import ENDPOINT_METADATA, register_endpoint

from ..data.basic import write_json
from ..data.schema import Account, PluginRun
from ..webserver.webserver import WebServer
from .authenticators.credentials import PLUGIN_DIR
from .listeners import get_abort_plugin_listener, get_pod_restart_listener
from .states import RUN_COMPLETED, RUN_DAEMON, RUN_INITIALIZED, RUN_STARTED


class PluginBase(metaclass=ABCMeta):
    """Base class for plugins"""

    schema_classes = []

    def __init__(self, pluginRun: PluginRun = None, *, client: PodClient, **kwargs):
        super().__init__()
        if pluginRun is None:
            warnings.warn(
                "Plugin needs a pluginRun as kwarg, running without will only work in development.",
                RuntimeWarning,
            )
        self.pluginRun = pluginRun

        if client is None:
            raise ValueError("Plugins need a `client: PodClient` as kwarg to run.")
        self.client = client
        self._status_listeners = []
        self._config_dict = kwargs
        self._daemon = False

        if pluginRun is None:
            self._webserver = WebServer(8080)
        else:
            self._webserver = WebServer(pluginRun.webserverPort or 8080)

        self.endpoints = self._get_endpoint_methods()
        self._register_api_endpoints()

        self.set_run_status(RUN_INITIALIZED)

    def set_run_status(self, status):
        # TODO sync before setting status (requires pod_client.sync())
        if self.pluginRun and self.client:
            self.pluginRun.status = status
            self.client.update_item(self.pluginRun)

        self._status = status

    def set_progress(self, progress):
        if self.pluginRun and self.client:
            self.pluginRun.progress = progress
            self.client.update_item(self.pluginRun)

    def setup(self):
        if self.client and self.pluginRun:
            status_abort_listener = get_abort_plugin_listener(self.client, self.pluginRun.id)
            pod_restart_listener = get_pod_restart_listener(self.client, self.pluginRun.id)
            self._status_listeners.extend([status_abort_listener, pod_restart_listener])

        self._webserver.run()

    def teardown(self):
        for listener in self._status_listeners:
            listener.stop()

        self._webserver.shutdown()

    def _run(self):
        self.set_run_status(RUN_STARTED)

        self.setup()
        self.run()

        if self.daemon:
            self.set_run_status(RUN_DAEMON)
        else:
            self.teardown()
            self.set_run_status(RUN_COMPLETED)

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError()

    def add_to_schema(self):
        """
        Add all schema classes required by the plugin to self.client here.
        """
        if len(self.schema_classes):
            self.client.add_to_schema(*self.schema_classes)

    @classmethod
    def get_schema(cls):
        schema = []
        for schema_cls in cls.schema_classes:
            schema.extend(schema_cls.pod_schema())
        return schema

    def _register_api_endpoints(self):
        """Collect decorated methods and add them to the webserver routes"""
        for (path, method), endpoint in self.endpoints.items():
            self._webserver.app.add_api_route(path=path, endpoint=endpoint, methods=[method])

    def _get_endpoint_methods(self):
        """Collect decorated methods, bind them with `self`, and store in `endpoints`"""
        endpoints = {}
        for _method_name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, ENDPOINT_METADATA):
                metadata = method.__endpoint_metadata__

                if metadata in endpoints:
                    raise RuntimeError(
                        f"endpoint {metadata[0]} with method {metadata[1]} is already registered"
                    )

                endpoints[metadata] = method

        return endpoints

    @register_endpoint("/v1/health", "GET")
    def health_endpoint(self):
        """Returns current state of the plugin"""
        return self._status

    @register_endpoint("/v1/api", "GET")
    def get_public_api(self):
        """Returns exposed functions of the plugin"""

        def get_friendly_annotation_name(kv):
            """Annotation can be done by class, like: int, list, str
            or by alias from typing module, like List, Sequence, Tuple.
            """
            k, v = kv
            if hasattr(v, "__name__"):
                # For classes, use __name__ that returns
                # more concise value
                return (k, v.__name__)
            else:
                # The typing aliases do not provide __name__ attribute, so use
                # __repr__ implementation.
                return (k, str(v))

        resp = {
            func_name: {
                "method": method,
                "args": dict(
                    map(
                        get_friendly_annotation_name,
                        inspect.getfullargspec(func).annotations.items(),
                    )
                ),
            }
            for ((func_name, method), func) in self.endpoints.items()
        }
        return resp

    @property
    def daemon(self) -> bool:
        return self._daemon

    @daemon.setter
    def daemon(self, daemon: bool):
        """Setting to True will not close the plugin after calling run(), default if False"""
        self._daemon = daemon


class PluginError(Exception):
    """Generic class for plugin errors. This error is raised when a plugin raises an unexpected exception."""

    pass


def write_run_info(plugin, id_):
    try:
        if plugin is None:
            raise ValueError("Empty container")
        run_path = PLUGIN_DIR / plugin / "current_run.json"
        run_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"writing run info to {run_path}")
        write_json({"id": id_}, run_path)
    except Exception as e:
        logger.error(f"""failed to write run info to {run_path}\n{e}""")


def get_plugin_cls(plugin_module, plugin_name):
    try:
        module = importlib.import_module(plugin_module)
        plugin_cls = getattr(module, plugin_name)
        return plugin_cls
    except (ImportError, AttributeError):
        raise ImportError(f"Unknown plugin: {plugin_module}.{plugin_name}")


def run_plugin_from_run_id(run_id, client, **kwargs):
    """
    Runs a plugin from run_id, initialized with **kwargs.

    Args:
        client (PodClient): client containing PluginRun
        run_id (int): id of the PluginRun
    """

    run = client.get(run_id)
    write_run_info(
        run.pluginModule.split(".")[0] if run.pluginModule is not None else run.containerImage,
        run.id,
    )

    plugin_cls = get_plugin_cls(run.pluginModule, run.pluginName)
    plugin = plugin_cls(pluginRun=run, client=client, **kwargs)
    plugin.add_to_schema()

    plugin._run()

    return plugin


def parse_metadata(fn, remove_container=False):
    metadata = read_json(fn)
    for k in ["pluginModule", "pluginName"]:
        if k not in metadata:
            raise ValueError(f"Missing metadata: {k}")

    run_vars = {k: v for k, v in metadata.items() if k in PluginRun.properties}
    run = PluginRun.from_json(run_vars)
    if remove_container:
        run.containerImage = "none"

    if "account" in metadata:
        account = Account.from_json(metadata["account"])
        run.add_edge("account", account)
    return run


def parse_config(run_config, config_file=None, remove_container=False):
    """
    Parse the configuration of the plugin. A configuration is a dict that is passed to the plugin init as kwargs.
    If configuration file is defined, the run_config is ignored.
    """
    if config_file is not None:
        config = read_json(config_file)
    elif isinstance(run_config, str) and len(run_config):
        config = json.loads(run_config)
    else:
        config = dict()

    if not isinstance(config, dict):
        raise ValueError(f"Incorrect plugin config format, expected a dict, got a {type(config)}")
    return config


def create_run_expanded(client, run):
    client.create(run)
    accounts = run.account
    if accounts:
        account = accounts[0]
        client.create(account)
        client.create_edge(run.get_edges("account")[0])
