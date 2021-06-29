# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.pluginbase.ipynb (unless otherwise specified).

__all__ = ['POD_FULL_ADDRESS_ENV', 'POD_TARGET_ITEM_ENV', 'POD_OWNER_KEY_ENV', 'POD_AUTH_JSON_ENV', 'PluginBase',
           'PluginRun', 'MyItem', 'MyPlugin', 'get_plugin', 'run_plugin_from_run_id', 'register_base_schemas',
           'run_plugin', 'run_plugin_from_pod']

# Cell
from ..data.schema import *
from ..pod.client import PodClient, DEFAULT_POD_ADDRESS
from ..imports import *
from os import environ
from abc import ABCMeta
import abc
import json
import importlib
import string
from enum import Enum
from ..pod.client import PodClient
from fastscript import *
import os

# Cell
POD_FULL_ADDRESS_ENV        = 'POD_FULL_ADDRESS'
POD_TARGET_ITEM_ENV         = 'POD_TARGET_ITEM'
POD_OWNER_KEY_ENV           = 'POD_OWNER'
POD_AUTH_JSON_ENV           = 'POD_AUTH_JSON'

# Cell
# hide
class PluginBase(Item, metaclass=ABCMeta):
    """Base class for plugins"""
    properties = Item.properties + ["name", "repository", "icon", "data_query", "bundleImage",
                                    "runDestination", "pluginClass"]
    edges = Item.edges + ["PluginRun"]

    def __init__(self, name=None, repository=None, icon=None, query=None, bundleImage=None, runDestination=None,
                 pluginClass=None, indexerRun=None, **kwargs):
        if pluginClass is None: pluginClass=self.__class__.__name__
        super().__init__(**kwargs)
        self.name = name
        self.repository = repository
        self.icon = icon
        self.query = query
        self.bundleImage = bundleImage
        self.runDestination = runDestination
        self.pluginClass = pluginClass
        self.indexerRun = indexerRun if indexerRun is not None else []

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_to_schema(self):
        raise NotImplementedError()

# Cell
# hide
class PluginRun(Item):
    properties = Item.properties + ["targetItemId", "pluginModule", "pluginName", "config", "containerImage",
                                    "state"]
    edges = PluginBase.edges

    def __init__(self, containerImage, pluginModule, pluginName, config="", state=None, targetItemId=None,
                 **kwargs):
        """
                PluginRun defines a the run of plugin `plugin_module.plugin_name`,
        with an optional `config` string.

        Args:
            plugin_module (str): module of the plugin.
            plugin_name (str): class name of the plugin.
            config (str, optional): Optional plugin configuration. For example,
                this could be a `json.dumps` of a configuration dict. Defaults to None.
        """
        super().__init__(**kwargs)
        self.pluginModule = pluginModule
        self.pluginName = pluginName
        self.config = config
        self.containerImage=containerImage
        id_ = "".join([random.choice(string.hexdigits) for i in range(32)]) if targetItemId is None else targetItemId
        self.targetItemId=id_
        self.id=id_
        self.state=state

# Cell
# hide
class MyItem(Item):
    properties = Item.properties + ["name", "age"]
    edges = Item.edges
    def __init__(self, name=None, age=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.age = age

class MyPlugin(PluginBase):
    """"""
    properties = PluginBase.properties + ["containerImage"]
    edges= PluginBase.edges

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, run, client):
        print("running")
        client.create(MyItem("some person", 20))

    def add_to_schema(self, client):
        client.add_to_schema(MyItem("my name", 10))

# Cell
# export
def get_plugin(plugin_module, plugin_name):
    try:
        module = importlib.import_module(plugin_module)
        plugin_cls = getattr(module, plugin_name)
        return plugin_cls()
    except (ImportError, AttributeError):
        raise ImportError(f"Unknown plugin: {plugin_module}.{plugin_name}")

def run_plugin_from_run_id(run_id, client, return_plugin=False):
    """
    Args:
        run_id (int): id of the PluginRun
        client (PodClient): client containing PluginRun
        return_plugin (bool): Returns created plugin instance for testing purposes.
    """
    run = client.get(run_id)
    plugin = get_plugin(run.pluginModule, run.pluginName)
    plugin.add_to_schema(client)
    plugin.run(run, client)

    return plugin if return_plugin else None

# Cell
# hide
def register_base_schemas(client):
    try:
        assert client.add_to_schema(PluginRun("", "", "", "", ""))
    except Exception as e:
        raise ValueError("Could not add base schema")

# Cell
def _run_plugin(client, plugin_run_id=None, verbose=False):
    """Runs an plugin, you can either provide the run settings as parameters to this function (for local testing)
    or via environment variables (this is how the pod communicates with plugins)."""
    register_base_schemas(client)
    run_plugin_from_run_id(plugin_run_id, client)

# Cell
# hide
def _parse_env(env):
    try:
        pod_full_address = env.get(POD_FULL_ADDRESS_ENV, DEFAULT_POD_ADDRESS)
        plugin_run_json  = json.loads(str(env[POD_TARGET_ITEM_ENV]))
        print(plugin_run_json)
        plugin_run_id    = plugin_run_json["id"]
        owner_key        = env.get(POD_OWNER_KEY_ENV)
        pod_auth_json    = json.loads(str(env.get(POD_AUTH_JSON_ENV)))
#         database_key = pod_service_payload[DATABASE_KEY_ENV]
#         owner_key    = pod_service_payload[OWNER_KEY_ENV]
        return pod_full_address, plugin_run_id, pod_auth_json, owner_key
    except KeyError as e:
        raise Exception('Missing parameter: {}'.format(e)) from None


# Cell
@call_parse
def run_plugin(pod_full_address:Param("The pod full address", str)=None,
               plugin_run_id:Param("Run id of the plugin to be executed", str)=None,
               database_key:Param("Database key of the pod", str)=None,
               owner_key:Param("Owner key of the pod", str)=None,
               container:Param("Pod container to run frod", str)=None):

    env = os.environ
    params = [pod_full_address, plugin_run_id, database_key, owner_key]

    if all([p is None for p in params]):
        print("Reading `run_plugin()` parameters from environment variables")
        pod_full_address, plugin_run_id, pod_auth_json, owner_key = _parse_env(env)
        database_key=None
    else:
        print("Used arguments passed to `run_plugin()` (ignoring environment)")
        pod_auth_json=None
        if (None in params):
            raise ValueError(f"Defined some params to run indexer, but not all. Missing \
                             {[p for p in params if p is None]}")
    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key,
                       auth_json=pod_auth_json)
    for name, val in [("pod_full_address", pod_full_address), ("plugin_run_id", plugin_run_id),
                      ("owner_key", owner_key), ("auth_json", pod_auth_json)]:
        print(f"{name}={val}")
    print()
    _run_plugin(client=client, plugin_run_id=plugin_run_id)

# Cell
from fastcore.script import call_parse, Param
import os

@call_parse
def run_plugin_from_pod(pod_full_address:Param("The pod full address", str)=None,
                        database_key:Param("Database key of the pod", str)=None,
                        owner_key:Param("Owner key of the pod", str)=None,
                        container:Param("Pod container to run frod", str)=None,
                        plugin_module:Param("Plugin module", str)=None,
                        plugin_name:Param("Plugin class name", str)=None,
                        settings_file:Param("Plugin settings (json)", str)=None):
    params = [pod_full_address, database_key, owner_key, container, plugin_module, plugin_name]
    if (None in params):
        raise ValueError(f"Defined some params to run indexer, but not all. Missing \
                         {[p for p in params if p is None]}")
    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key)
    for name, val in [("pod_full_address", pod_full_address), ("owner_key", owner_key)]:
        print(f"{name}={val}")

    if settings_file is not None:
        with open(settings_file, 'r') as f:
            settings = f.read()
    else:
        settings = None

    register_base_schemas(client)
    run = PluginRun(container, plugin_module, plugin_name, settings)
    print(f"\ncalling the `create` api on {pod_full_address} to make your Pod start "
          f"a plugin with id {run.id}.")
    print(f"*Check the pod log/console for debug output.*")
    client.create(run)
    print(f"Created PluginRun: {run.id}")
    return run
