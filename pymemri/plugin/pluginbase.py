# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.pluginbase.ipynb (unless otherwise specified).

__all__ = ['POD_FULL_ADDRESS_ENV', 'RUN_UID_ENV', 'POD_SERVICE_PAYLOAD_ENV', 'DATABASE_KEY_ENV', 'OWNER_KEY_ENV',
           'PluginBase', 'PluginRun', 'MyPlugin', 'run_plugin_from_run_id', 'register_base_classes', 'run_plugin']

# Cell
from ..data.schema import *
from ..pod.client import PodClient, DEFAULT_POD_ADDRESS
from ..imports import *
from os import environ

# Cell
POD_FULL_ADDRESS_ENV    = 'POD_FULL_ADDRESS'
RUN_UID_ENV             = 'RUN_ID'
POD_SERVICE_PAYLOAD_ENV = 'POD_SERVICE_PAYLOAD'
DATABASE_KEY_ENV        = 'databaseKey'
OWNER_KEY_ENV           = 'ownerKey'

# Cell
# hide
class PluginBase(Item):
    """Base class for plugins"""
    properties = Item.properties + ["name", "repository", "icon", "data_query", "bundleImage",
                                    "runDestination", "pluginClass", "pluginPackage"]
    edges = Item.edges + ["IndexerRun"]

    def __init__(self, name=None, repository=None, icon=None, query=None, bundleImage=None, runDestination=None,
                 pluginClass=None, indexerRun=None, **kwargs):
        if pluginClass is None: pluginClass=self.__class__.__name__
        self.pluginPackage=None
        super().__init__(**kwargs)
        self.name = name
        self.repository = repository
        self.icon = icon
        self.query = query
        self.bundleImage = bundleImage
        self.runDestination = runDestination
        self.pluginClass = pluginClass
        self.indexerRun = indexerRun if indexerRun is not None else []

    def run(self):
        raise NotImplementedError()

# Cell
# hide
class PluginRun(Item):
    properties = Item.properties
    edges = Item.edges + ["plugin"]

    def __init__(self, plugin=None, **kwargs):
        super().__init__(**kwargs)
        self.plugin=plugin if plugin is not None else []

# Cell
# hide
class MyPlugin(PluginBase):
    """"""
    properties = PluginBase.properties
    edges= PluginBase.edges

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pluginPackage="pymemri.plugin.pluginbase"

    def run(self, run, client):
        print("running")

# Cell
# export
def run_plugin_from_run_id(run_id, client):
    run = client.get(run_id)
    plugins = run.plugin
    if len(plugins) == 0:
        raise ValueError(f"plugin run {run_id} has no plugin attached to it. Make sure there is a 'plugin' \
                           edge from your run to the actual plugin object.")
    plugin = plugins[0]
    plugin.run(run, client)

# Cell
# hide
def register_base_classes(client):
    try:
        assert client.add_to_schema(PluginRun())
    except Exception as e:
        raise ValueError("Could not add base schema")

# Cell
def _run_plugin(pod_full_address=None, plugin_run_id=None, database_key=None, owner_key=None,
                   verbose=False):
    """Runs an plugin, you can either provide the run settings as parameters to this function (for local testing)
    or via environment variables (this is how the pod communicates with plugins)."""
    if verbose:
        for name, val in [("pod_full_address", pod_full_address), ("plugin_run_id", plugin_run_id),
                  ("database_key", database_key), ("owner_key", owner_key)]:
            print(f"{name}={val}")
        print()

    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key)
    register_base_classes(client)
    run_plugin_from_run_id(plugin_run_id, client)


# Cell
# hide
def _parse_env(env):
    try:
        pod_full_address = env.get(POD_FULL_ADDRESS_ENV, DEFAULT_POD_ADDRESS)
        plugin_run_id  = str(env[RUN_UID_ENV])
        pod_service_payload = json.loads(env[POD_SERVICE_PAYLOAD_ENV])

        database_key = pod_service_payload[DATABASE_KEY_ENV]
        owner_key    = pod_service_payload[OWNER_KEY_ENV]
        return pod_full_address, plugin_run_id, pod_service_payload, database_key, owner_key
    except KeyError as e:
        raise Exception('Missing parameter: {}'.format(e)) from None


# Cell
from fastscript import *
import os

@call_parse
def run_plugin(pod_full_address:Param("The pod full address", str)=None,
               plugin_run_id:Param("Run id of the plugin to be executed", str)=None,
               database_key:Param("Database key of the pod", str)=None,
               owner_key:Param("Owner key of the pod", str)=None):

    env = os.environ
    params = [pod_full_address, plugin_run_id, database_key, owner_key]

    if all([p is None for p in params]):
        print("Reading `run_plugin()` parameters from environment variables")
        pod_full_address, plugin_run_id, pod_service_payload, database_key, owner_key = _parse_env(env)
    else:
        print("Used arguments passed to `run_plugin()` (ignoring environment)")
        if (None in params):
            raise ValueError(f"Defined some params to run indexer, but not all. Missing \
                             {[p for p in params if p is None]}")

    _run_plugin(pod_full_address=pod_full_address, plugin_run_id=plugin_run_id,
                   database_key=database_key, owner_key=owner_key, verbose=True)