# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.schema.ipynb (unless otherwise specified).

__all__ = ['Account', 'PluginRun', 'PersistentState']

# Cell
# hide
import random, string
from ..data.itembase import Item

# Cell
# hide
class Account(Item):

    properties = Item.properties + ['service', "identifier", "secret", "code", "refreshToken", "errorMessage"]
    edges = Item.edges


    def __init__(self, service=None, identifier=None, secret=None, code=None, refreshToken=None,
                 errorMessage=None, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.identifier = identifier
        self.secret = secret
        self.refreshToken = refreshToken
        self.code = code
        self.errorMessage = errorMessage

# Cell
# hide
class PluginRun(Item):
    properties = Item.properties + ["containerImage", "pluginModule", "pluginName", "state", "targetItemId",
                                    "authUrl", "error", "settings"]
    edges = Item.edges + ["view", "persistentState", "account"]

    def __init__(self, containerImage, pluginModule, pluginName, state=None, settings=None, view=None,
                 targetItemId=None, authUrl=None, error=None, persistentState=None, account=None,
                 **kwargs):
        """
                PluginRun defines a the run of plugin `plugin_module.plugin_name`,
        with an optional `settings` string.

        Args:
            plugin_module (str): module of the plugin.
            plugin_name (str): class name of the plugin.
            settings (str, optional): Optional plugin configuration. For example,
                this could be a `json.dumps` of a configuration dict. Defaults to None.
        """
        super().__init__(**kwargs)
        self.pluginModule = pluginModule
        self.pluginName = pluginName
        self.containerImage=containerImage
        id_ = "".join([random.choice(string.hexdigits) for i in range(32)]) if targetItemId is None else targetItemId
        self.targetItemId=id_
        self.id=id_
        self.status = state       # for stateful plugins
        self.settings = settings
        self.authUrl = authUrl # for authenticated plugins
        self.error = error # universa
        self.account = account if account is not None else []
        self.persistentState = persistentState if persistentState is not None else []
        self.view = view if view is not None else []

# Cell
# hide
class PersistentState(Item):
    """ Persistent state variables saved for plugin such as views, accounts, the last state to resume from etc. """

    properties = Item.properties + ["pluginId", "state"]
    edges = Item.edges + ["account", "view"]

    def __init__(self, pluginName=None, state=None, account=None, view=None, **kwargs):
        super().__init__(**kwargs)
        self.pluginName = pluginName
        self.status = state
        self.account = account if account is not None else []
        self.view = view if view is not None else []

    def get_state(self):
        return self.status

    def set_state(self, client, state_str):
        self.status = state_str
        client.update_item(self)

    def get_account(self):
        if len(self.account) == 0:
            return None
        else:
            return self.account[0]

    def set_account(self, client, account):
        if len(self.account) == 0:
            if not account.id:
                client.create(account)
            self.add_edge('account', account)
            self.update(client)
        else:
            existing_account = self.account[0]
            for prop in account.properties:
                value = getattr(account, prop, None)
                if value and hasattr(existing_account, prop):
                    setattr(existing_account, prop, value)
            existing_account.update(client)

    def get_view_by_name(self, view_name):
        for cvu in self.view:
            if cvu.name == view_name:
                return cvu

    def set_views(self, client, views=None):
        for view in views:
            client.create(view)
            self.add_edge('view', view)
        self.update(client)
        return True