# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.pluginbase.ipynb (unless otherwise specified).

__all__ = ['POD_FULL_ADDRESS_ENV', 'POD_TARGET_ITEM_ENV', 'POD_OWNER_KEY_ENV', 'POD_AUTH_JSON_ENV', 'PluginBase',
<<<<<<< HEAD
           'MyAPIClient', 'MyItem', 'MyPlugin', 'get_plugin_cls', 'run_plugin_from_run_id', 'store_keys',
=======
           'MyItem', 'MyPlugin', 'get_plugin_cls', 'get_plugin_state', 'run_plugin_from_run_id', 'store_keys',
>>>>>>> dev
           'parse_config', 'create_run_expanded', 'run_plugin', 'simulate_run_plugin_from_frontend']

# Cell
from ..data.schema import *
from ..pod.client import *
from ..imports import *
from ..pod.utils import *
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
<<<<<<< HEAD
from .schema import Account, PluginRun
=======
from .schema import PluginRun, PersistentState, Account
>>>>>>> dev
from ..data.basic import *

from typing import Any

# Cell
POD_FULL_ADDRESS_ENV        = 'POD_FULL_ADDRESS'
POD_TARGET_ITEM_ENV         = 'POD_TARGET_ITEM'
POD_OWNER_KEY_ENV           = 'POD_OWNER'
POD_AUTH_JSON_ENV           = 'POD_AUTH_JSON'

# Cell
# hide
class PluginBase(Item, metaclass=ABCMeta):
    """Base class for plugins"""
    properties = Item.properties + ["name", "repository", "icon", "query", "bundleImage",
                                    "runDestination", "pluginClass", "client", "pluginRun"]
    edges = Item.edges

    def __init__(self, client=None, pluginRun=None, name=None, repository=None, icon=None,
                 query=None, bundleImage=None, runDestination=None, pluginClass=None, **kwargs):
        if pluginClass is None: pluginClass=self.__class__.__name__
        super().__init__(**kwargs)
        self.client = client
        self.pluginRun = pluginRun
        self.name = name
        self.repository = repository
        self.icon = icon
        self.query = query
        self.bundleImage = bundleImage
        self.runDestination = runDestination
        self.pluginClass = pluginClass

    def get_run(self):
        return self.client.get(self.run_id, expanded=False)

    def get_state(self):
        return self.get_run().state

    def get_account(self):
        run = self.get_run()
        return run.account[0] if len(run.account) > 0 else None

    def get_settings(self):
        run = self.get_run(self.client)
        return json.loads(run.settings)

    def set_vars(self, vars):
        run = self.get_run()
        for k,v in vars.items():
            if hasattr(run, k):
                setattr(run, k, v)
        run.update(self.client)

    def set_state(self, state, message=None):
        self.set_vars({'state': state, 'message': message})

    def set_account(self, account):
        existing = self.get_account()
        if existing:
            account.id = existing.id
            account.update(self.client)
        else:
            run = self.get_run()
            run.add_edge('account', account)
            run.update(self.client)

    def set_settings(self, settings):
        self.set_vars({'settings': json.dumps(settings)})

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_to_schema(self):
        raise NotImplementedError()

# Cell
# hide

from .authenticators.oauth import ExampleOAuthAuthenticator

class MyAPIClient:
    def __init__(self, accessToken):
        self.access_token = accessToken

    def get_data(self):
        return [{'name': 'name_1', 'age': 21}, {'name': 'name_2', 'age': 22}]

class MyItem(Item):
    properties = Item.properties + ["name", "age"]
    edges = Item.edges
    def __init__(self, name=None, age=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.age = age

class MyPlugin(PluginBase):
    """"""
    properties = PluginBase.properties
    edges= PluginBase.edges

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        print("running")
        self.login()
<<<<<<< HEAD
        items = self.api.get_data()
        for item in items:
            self.client.create(MyItem(name=item['name'], age=item['age']))

    def login(self):
        auth = ExampleOAuthAuthenticator(self.client, self.pluginRun)
        auth.set_test(True)
        auth.authenticate()
        self.api = MyAPIClient(self.pluginRun.account[0].secret)

    def add_to_schema(self):
        self.client.add_to_schema(MyItem("my name", 10))

=======
        client.create(MyItem("some person", 20))

    def login(self):
        account = self.pluginRun.account[0]
        print(f"logging in with account {account.identifier} and password {account.secret}")

    def add_to_schema(self, client):
        client.add_to_schema(MyItem("my name", 10))
>>>>>>> dev

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
    plugin_cls = get_plugin_cls(run.pluginModule, run.pluginName)
    plugin = plugin_cls(client=client, pluginRun=run)
    plugin.add_to_schema()

    # TODO handle plugin status before run
    plugin.run()

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

    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key,
                       auth_json=pod_auth_json)

    if config_file is not None:
        run = parse_config(config_file, remove_container=True)
        create_run_expanded(client, run)
        plugin_run_id=run.id

    print(f"pod_full_address={pod_full_address}\nowner_key={owner_key}\n")

    run_plugin_from_run_id(run_id=plugin_run_id, client=client)

# Cell
from fastcore.script import call_parse, Param
import os

@call_parse
def simulate_run_plugin_from_frontend(pod_full_address:Param("The pod full address", str)=DEFAULT_POD_ADDRESS,
                        database_key:Param("Database key of the pod", str)=None,
                        owner_key:Param("Owner key of the pod", str)=None,
                        container:Param("Pod container to run frod", str)=None,
                        plugin_path:Param("Plugin path", str)=None,
                        settings_file:Param("Plugin settings (json)", str)=None,
<<<<<<< HEAD
                        config_file:Param("config file for the PluginRun", str)=None,
                        account_id:Param("Account id to be used inside the plugin", str)=None):

=======
                        config_file:Param("config file for the PluginRun", str)=None):
>>>>>>> dev
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

#     if settings_file is not None:
#         with open(settings_file, 'r') as f:
#             settings = f.read()
#     else:
#         settings = None

<<<<<<< HEAD
    if account_id is None:
        account = None
    else:
        account = client.get(account_id)
        print(f"Using {account}")

    register_base_schemas(client)
    run = PluginRun(container, plugin_module, plugin_name, account=[account])

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
=======
    if config_file is not None:
        run = parse_config(config_file)
        create_run_expanded(client, run)
>>>>>>> dev

    else:
        if container is None:
            container = plugin_path.split(".", 1)[0]
        print(f"Inferred '{container}' as plugin container name")
        plugin_module, plugin_name = plugin_path.rsplit(".", 1)
        run = PluginRun(container, plugin_module, plugin_name)
        if plugin_id is not None:
            persistent_state = client.get(plugin_id)
            run.add_edge("persistentState", persistent_state)
            client.create_edge(run.get_edges("persistentState")[0])
            client.create(run)
    print(f"\ncalling the `create` api on {pod_full_address} to make your Pod start "
          f"a plugin with id {run.id}.")
    print(f"*Check the pod log/console for debug output.*")
    return run