# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.pluginbase.ipynb (unless otherwise specified).

__all__ = ['POD_FULL_ADDRESS_ENV', 'POD_TARGET_ITEM_ENV', 'POD_OWNER_KEY_ENV', 'POD_AUTH_JSON_ENV',
           'POD_PLUGIN_DNS_ENV', 'PluginBase', 'PluginError', 'ExamplePlugin', 'write_run_info', 'get_plugin_cls',
           'run_plugin_from_run_id', 'store_keys', 'parse_metadata', 'parse_config', 'create_run_expanded',
           'run_plugin', 'simulate_run_plugin_from_frontend']

# Cell
from ..data.schema import *
from ..pod.client import *
from ..imports import *
from .states import *
from ..pod.utils import *
from .listeners import get_abort_plugin_listener, get_delete_plugin_listener
from ..webserver.webserver import WebServer

from os import environ
from abc import ABCMeta
import abc
import json
import importlib
import string
import time
from enum import Enum
from fastscript import *
import os
from .schema import Account, PluginRun
from ..data.basic import *
from ..pod.client import Dog, PodClient, DEFAULT_POD_ADDRESS
import warnings
from ..data.basic import write_json
from .authenticators.credentials import PLUGIN_DIR
from fastcore.script import call_parse, Param
import os
import traceback

# Cell
POD_FULL_ADDRESS_ENV        = 'POD_FULL_ADDRESS'
POD_TARGET_ITEM_ENV         = 'POD_TARGET_ITEM'
POD_OWNER_KEY_ENV           = 'POD_OWNER'
POD_AUTH_JSON_ENV           = 'POD_AUTH_JSON'
POD_PLUGIN_DNS_ENV          = 'PLUGIN_DNS'

# Cell
class PluginBase(metaclass=ABCMeta):
    """Base class for plugins"""

    schema_classes = []

    def __init__(self, pluginRun=None, client=None, **kwargs):
        super().__init__()
        if pluginRun is None:
            warnings.warn(
                "Plugin needs a pluginRun as kwarg, running without will only work in development.",
                RuntimeWarning)
        self.pluginRun = pluginRun

        if client is None:
            raise ValueError("Plugins need a `client: PodClient` as kwarg to run.")
        self.client = client
        self._status_listeners = []
        self._config_dict = kwargs

        if pluginRun is None:
            self._webserver = WebServer(8080)
        else:
            self._webserver = WebServer(pluginRun.webserverPort or 8080)

        self.set_run_status(RUN_INITIALIZED)

    def set_run_status(self, status):
        # TODO sync before setting status (requires pod_client.sync())
        if self.pluginRun and self.client:
            self.pluginRun.status = status
            self.client.update_item(self.pluginRun)

    def set_progress(self, progress):
        if self.pluginRun and self.client:
            self.pluginRun.progress = progress
            self.client.update_item(self.pluginRun)

    def setup(self):
        if self.client and self.pluginRun:
            status_abort_listener = get_abort_plugin_listener(self.client, self.pluginRun.id)
            self._status_listeners.append(status_abort_listener)

            delete_listener = get_delete_plugin_listener(self.client, self.pluginRun.id)
            self._status_listeners.append(delete_listener)


        self._webserver.run()

    def teardown(self):
        for listener in self._status_listeners:
            listener.stop()

    def _run(self):
        self.set_run_status(RUN_STARTED)

        self.setup()
        self.run()

        if self._webserver.is_running():
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
    def get_schema_properties(cls):
        schema = []
        for item in cls.schema_classes:
            item_schema = PodClient._property_dicts_from_type(item)
            schema.extend(item_schema)
        return schema

    @classmethod
    def get_schema_edges(cls):
        schema = []
        for item in cls.schema_classes:
            edge_types = item.get_edge_types()
            edge_schema = [
                {"type": "ItemEdgeSchema",
                 "edgeName": k,
                 "sourceType": s,
                 "targetType": t}
                for (k, s, t) in edge_types
            ]
            schema.extend(edge_schema)
        return schema

    @classmethod
    def get_schema(cls, include_edges: bool = True):
        schema = cls.get_schema_properties()
        if include_edges:
            edges = cls.get_schema_edges()
            schema.extend(edges)
        return schema

# Cell
# hide
class PluginError(Exception):
    """Generic class for plugin errors. This error is raised when a plugin raises an unexpected exception."""
    pass

# Cell
# hide
class ExamplePlugin(PluginBase):
    schema_classes = [Dog, Message]

    def __init__(self, dog_name: str = "Bob", **kwargs):
        super().__init__(**kwargs)
        self.dog_name = dog_name

    def run(self):
        print("Started plugin run...")
        dog = Dog(self.dog_name, 10)
        self.client.create(dog)
        print("Run success!")

# Cell
# hide
def write_run_info(plugin, id_):
    try:
        if plugin is None:
            raise ValueError("Empty container")
        run_path = PLUGIN_DIR / plugin / "current_run.json"
        run_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"writing run info to {run_path}")
        write_json({"id": id_}, run_path)
    except Exception as e:
        print(f"""failed to write run info to {run_path}\n{e}""")

# Cell
# export
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
    write_run_info(run.pluginModule.split(".")[0] if run.pluginModule is not None else run.containerImage, run.id)

    plugin_cls = get_plugin_cls(run.pluginModule, run.pluginName)
    plugin = plugin_cls(pluginRun=run, client=client, **kwargs)
    plugin.add_to_schema()

    plugin._run()

    return plugin

# Cell
# hide
def _parse_env():
    env = os.environ
    print("Reading `run_plugin()` parameters from environment variables")
    try:
        pod_full_address = env.get(POD_FULL_ADDRESS_ENV, DEFAULT_POD_ADDRESS)
        plugin_run_json  = json.loads(str(env[POD_TARGET_ITEM_ENV]))
        print(plugin_run_json)
        plugin_run_id    = plugin_run_json["id"]
        owner_key        = env.get(POD_OWNER_KEY_ENV)
        pod_auth_json    = json.loads(str(env.get(POD_AUTH_JSON_ENV)))
        return pod_full_address, plugin_run_id, pod_auth_json, owner_key
    except KeyError as e:
        raise Exception('Missing parameter: {}'.format(e)) from None

# Cell
# hide
@call_parse
def store_keys(path:Param("path to store the keys", str)=DEFAULT_POD_KEY_PATH,
               database_key:Param("Database key of the pod", str)=None,
               owner_key:Param("Owner key of the pod", str)=None,
               replace: Param("Replace existing stored keys", str)=True):

    if not replace:
        try:
            read_pod_key("database_key")
            read_pod_key("owner_key")
            print("Existing stored keys found, exiting without generating new keys.")
            return
        except ValueError:
            pass

    if database_key is None: database_key = PodClient.generate_random_key()
    if owner_key is None: owner_key = PodClient.generate_random_key()

    obj = {"database_key": database_key,
           "owner_key": owner_key}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        timestr = time.strftime("%Y%m%d-%H%M%S")
        path.rename(POD_KEYS_FULL_FOLDER / f"keys-{timestr}.json")
    write_json(obj, path)

# Cell
# hide
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
        account=accounts[0]
        client.create(account)
        client.create_edge(run.get_edges("account")[0])

# Cell
@call_parse
def run_plugin(
    pod_full_address: Param("The pod full address", str) = DEFAULT_POD_ADDRESS,
    plugin_run_id: Param("Run id of the plugin to be executed", str) = None,
    database_key: Param("Database key of the pod", str) = None,
    owner_key: Param("Owner key of the pod", str) = None,
    read_args_from_env: Param("Read the args from the environment", bool) = False,
    metadata: Param("metadata file for the PluginRun", str) = None,
    config_file: Param(
        "A plugin configuration, overwrites the configuration of the PluginRun", str
    ) = None,
):

    if read_args_from_env:
        pod_full_address, plugin_run_id, pod_auth_json, owner_key = _parse_env()
        database_key = None
    else:
        if database_key is None:
            database_key = read_pod_key("database_key")
        if owner_key is None:
            owner_key = read_pod_key("owner_key")
        pod_auth_json = None
    if POD_PLUGIN_DNS_ENV in os.environ:
        print(f"Plugin accessible via {os.environ.get(POD_PLUGIN_DNS_ENV)}:8080")

    client = PodClient(
        url=pod_full_address,
        database_key=database_key,
        owner_key=owner_key,
        auth_json=pod_auth_json,
    )
    print(f"pod_full_address={pod_full_address}\nowner_key={owner_key}\n")

    if metadata is not None:
        run = parse_metadata(metadata, remove_container=True)
        create_run_expanded(client, run)
        plugin_run_id = run.id
    else:
        run = client.get(plugin_run_id)
    plugin_config = parse_config(run.config, config_file)

    try:
        run_plugin_from_run_id(
            plugin_run_id, client, **plugin_config
        )
    except Exception as e:
        run = client.get(plugin_run_id)
        run.status = RUN_FAILED
        client.update_item(run)
        print(traceback.format_exc(), flush=True)
        raise PluginError("The plugin quit unexpectedly.") from None

# Cell
@call_parse
def simulate_run_plugin_from_frontend(
    pod_full_address: Param("The pod full address", str) = DEFAULT_POD_ADDRESS,
    database_key: Param("Database key of the pod", str) = None,
    owner_key: Param("Owner key of the pod", str) = None,
    container: Param("Pod container to run frod", str) = None,
    plugin_path: Param("Plugin path", str) = None,
    metadata: Param("metadata file for the PluginRun", str) = None,
    config_file: Param(
        "A plugin configuration, overwrites the configuration of the PluginRun", str
    ) = None,
    account_id: Param("Account id to be used inside the plugin", str) = None,
):
    if database_key is None:
        database_key = read_pod_key("database_key")
    if owner_key is None:
        owner_key = read_pod_key("owner_key")
    params = [pod_full_address, database_key, owner_key]
    if None in params:
        raise ValueError(f"Missing Pod credentials")

    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key)
    print(f"pod_full_address={pod_full_address}\nowner_key={owner_key}\n")

    if metadata is not None:
        run = parse_metadata(metadata)
        create_run_expanded(client, run)
    else:
        if container is None:
            container = plugin_path.split(".", 1)[0]
        print(f"Inferred '{container}' as plugin container name")
        plugin_module, plugin_name = plugin_path.rsplit(".", 1)
        run = PluginRun(container, plugin_module, plugin_name)

        if account_id is not None:
            account = client.get(account_id)
            run.add_edge("account", account)
            print(f"Using existing {account}")

        client.create(run)

    print(
        f"Created pluginrun with id {run.id} on {pod_full_address}"
    )

    plugin_dir = run.containerImage
    write_run_info(plugin_dir, run.id)

    print(f"*Check the pod log/console for debug output.*")
    return run