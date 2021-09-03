# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.pluginbase.ipynb (unless otherwise specified).

__all__ = ['POD_FULL_ADDRESS_ENV', 'POD_TARGET_ITEM_ENV', 'POD_OWNER_KEY_ENV', 'POD_AUTH_JSON_ENV',
           'POD_PLUGIN_DNS_ENV', 'PluginBase', 'ExamplePlugin', 'write_run_info', 'get_plugin_cls',
           'run_plugin_from_run_id', 'store_keys', 'parse_config', 'create_run_expanded', 'run_plugin',
           'simulate_run_plugin_from_frontend']

# Cell
from ..data.schema import *
from ..pod.client import *
from ..imports import *
from ..pod.utils import *
from .states import *

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
from ..pod.client import Dog, PodClient
import warnings
from ..data.basic import write_json
from .authenticators.credentials import PLUGIN_DIR
from fastcore.script import call_parse, Param
import os

# Cell
POD_FULL_ADDRESS_ENV        = 'POD_FULL_ADDRESS'
POD_TARGET_ITEM_ENV         = 'POD_TARGET_ITEM'
POD_OWNER_KEY_ENV           = 'POD_OWNER'
POD_AUTH_JSON_ENV           = 'POD_AUTH_JSON'
POD_PLUGIN_DNS_ENV          = 'PLUGIN_DNS'

# Cell
# hide
class PluginBase(metaclass=ABCMeta):
    """Base class for plugins"""

    def __init__(self, pluginRun=None, client=None, persistentState=None, **kwargs):
        super().__init__(**kwargs)

        if pluginRun is None:
            warnings.warn(
                "Plugin needs a pluginRun as kwarg, running without will only work while testing.",
                RuntimeWarning)
        self.pluginRun = pluginRun

        if client is None:
            raise ValueError("Plugins need a `client: PodClient` as kwarg to run.")
        self.client = client

        self.persistentState = persistentState

    def set_run_status(self, status):
        # TODO sync before setting status (requires pod_client.sync())
        if self.pluginRun and self.client:
            self.pluginRun.status = status
            self.client.update_item(self.pluginRun)

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_to_schema(self):
        """
        Add all schema classes required by the plugin to self.client here.
        """
        raise NotImplementedError()

# Cell
class ExamplePlugin(PluginBase):
    """"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        print("running")
        self.client.create(Dog("some dog", 20))

    def add_to_schema(self):
        self.client.add_to_schema(Dog("my name", 10))

# Cell
# hide
def write_run_info(plugin, id_):
    try:
        if plugin is None:
            raise ValueError("Empty container")
        run_path = PLUGIN_DIR / plugin / "current_run.json"
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

def run_plugin_from_run_id(run_id, client):
    """
    Args:
        run_id (int): id of the PluginRun
        client (PodClient): client containing PluginRun
        return_plugin (bool): Returns created plugin instance for testing purposes.
    """

    run = client.get(run_id)
    write_run_info(run.pluginModule.split(".")[0] if run.pluginModule is not None else run.containerImage, run.id)

    plugin_cls = get_plugin_cls(run.pluginModule, run.pluginName)
    plugin = plugin_cls(pluginRun=run, client=client)
    plugin.add_to_schema()

    plugin.set_run_status(RUN_STARTED)
    plugin.run()
    plugin.pluginRun = plugin.client.get(run_id)
    plugin.set_run_status(RUN_COMPLETED)

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
               owner_key:Param("Owner key of the pod", str)=None):

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
def parse_config(file, remove_container=False):
    json_dict = read_json(file)
    account = Account.from_json(json_dict["account"])
    del json_dict["account"]
    settings = json.dumps(json_dict["settings"])
    del json_dict["settings"]
    run = PluginRun.from_json(json_dict)
    run.settings = settings
    run.add_edge("account", account)
    if remove_container:
        run.containerImage = "none"
    return run

def create_run_expanded(client, run):
    client.create(run)
    accounts = run.account
    if accounts:
        account=accounts[0]
        client.create(account)
        client.create_edge(run.get_edges("account")[0])

# Cell
@call_parse
def run_plugin(pod_full_address:Param("The pod full address", str)=DEFAULT_POD_ADDRESS,
               plugin_run_id:Param("Run id of the plugin to be executed", str)=None,
               database_key:Param("Database key of the pod", str)=None,
               owner_key:Param("Owner key of the pod", str)=None,
               read_args_from_env:Param("Read the args from the environment", bool)=False,
               config_file:Param("config file for the PluginRun", str)=None):

    if read_args_from_env:
        pod_full_address, plugin_run_id, pod_auth_json, owner_key = _parse_env()
        database_key=None
    else:
        if database_key is None: database_key = read_pod_key("database_key")
        if owner_key is None: owner_key = read_pod_key("owner_key")
        pod_auth_json = None

    if POD_PLUGIN_DNS_ENV in os.environ:
        print(f"Plugin accesible via {os.environ.get(POD_PLUGIN_DNS_ENV)}:8080")

    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key,
                       auth_json=pod_auth_json)

    if config_file is not None:
        run = parse_config(config_file, remove_container=True)
        create_run_expanded(client, run)
        plugin_run_id=run.id

    print(f"pod_full_address={pod_full_address}\nowner_key={owner_key}\n")

    run_plugin_from_run_id(run_id=plugin_run_id, client=client)

# Cell
@call_parse
def simulate_run_plugin_from_frontend(pod_full_address:Param("The pod full address", str)=DEFAULT_POD_ADDRESS,
                        database_key:Param("Database key of the pod", str)=None,
                        owner_key:Param("Owner key of the pod", str)=None,
                        container:Param("Pod container to run frod", str)=None,
                        plugin_path:Param("Plugin path", str)=None,
                        settings_file:Param("Plugin settings (json)", str)=None,
                        config_file:Param("config file for the PluginRun", str)=None,
                        account_id:Param("Account id to be used inside the plugin", str)=None):

    # TODO remove container, plugin_module, plugin_name and move to Plugin item.
    # Open question: This presumes Plugin item is already in pod before simulate_run_plugin_from_frontend is called.
    if database_key is None: database_key = read_pod_key("database_key")
    if owner_key is None: owner_key = read_pod_key("owner_key")
    params = [pod_full_address, database_key, owner_key]

    if (None in params):
        raise ValueError(f"Defined some params to run indexer, but not all")
    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key)
    for name, val in [("pod_full_address", pod_full_address), ("owner_key", owner_key)]:
        print(f"{name}={val}")

    if config_file is not None:
        run = parse_config(config_file)
        create_run_expanded(client, run)
    else:
        if container is None:
            container = plugin_path.split(".", 1)[0]
        print(f"Inferred '{container}' as plugin container name")

        plugin_module, plugin_name = plugin_path.rsplit(".", 1)
        run = PluginRun(container, plugin_module, plugin_name)

        if account_id is not None:
            account = client.get(account_id)
            run.add_edge('account', account)
            print(f"Using existing {account}")

        client.create(run)

    print(f"\ncalling the `create` api on {pod_full_address} to make your Pod start "
          f"a plugin with id {run.id}.")

    plugin_dir = run.containerImage
    write_run_info(plugin_dir, run.id)

    print(f"*Check the pod log/console for debug output.*")
    return run