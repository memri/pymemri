# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.schema.ipynb (unless otherwise specified).

__all__ = ['Account', 'PluginRun']

# Cell
# hide
import random, string
from ..data.itembase import Item

# Cell
# hide
class Account(Item):

    properties = Item.properties + ['service', "identifier", "secret", "code", "accessToken", "refreshToken", "errorMessage"]
    edges = Item.edges + ['belongsTo', 'contact', 'price', 'location', 'organization']


    def __init__(self, handle=None, displayName=None, service=None, avatarUrl=None, identifier=None, secret=None, code=None, accessToken=None, refreshToken=None,
                 errorMessage=None, contact=None, belongsTo=None, price=None, location=None, organization=None, **kwargs):
        super().__init__(**kwargs)
        self.handle = handle
        self.displayName = displayName
        self.service = service
        self.avatarUrl = avatarUrl
        self.identifier = identifier
        self.secret = secret
        self.code = code
        self.accessToken = accessToken
        self.refreshToken = refreshToken
        self.errorMessage = errorMessage
        self.contact = contact if contact is not None else []
        self.belongsTo = belongsTo if belongsTo is not None else []
        self.price = price if price is not None else []
        self.location = location if location is not None else []
        self.organization = organization if organization is not None else []


# Cell
# hide
class PluginRun(Item):
    properties = Item.properties + ["containerImage", "pluginModule", "pluginName", "status", "targetItemId",
                                    "oAuthUrl", "message", "settings"]
    edges = Item.edges + ["account", "view"]

    def __init__(self, containerImage, pluginModule, pluginName, account=None, status=None, settings=None, targetItemId=None, oAuthUrl=None, message=None, view=None,
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
        self.containerImage = containerImage
        id_ = ''.join([random.choice(string.hexdigits) for i in range(32)]) if targetItemId is None else targetItemId
        self.targetItemId=id_
        self.id=id_
        self.status = status
        self.settings = settings
        self.oAuthUrl = oAuthUrl
        self.message = message

        self.account = account if account is not None else []
        self.view = view if view is not None else []

    def reload(self, client):
        self = client.get(self.id, expanded=True)
