import random
import string

from ._central_schema import *
from .dataset import Dataset
from .itembase import Edge, Item, ItemBase
from .photo import Photo


def get_constructor(_type, plugin_class=None, plugin_package=None, extra=None):
    import pymemri.integrator_registry

    from .photo import Photo

    if (
        _type == "Indexer"
        and plugin_class is not None
        and hasattr(pymemri.integrator_registry, plugin_class)
    ):
        return getattr(pymemri.integrator_registry, plugin_class)
    if plugin_class is not None and plugin_package is not None:
        try:
            mod = __import__(plugin_package, fromlist=[plugin_class])
            dynamic = {plugin_class: getattr(mod, plugin_class)}
        except Exception as e:
            print(f"Could not import {plugin_class}.{plugin_package}")
    else:
        dynamic = dict()

    classes = z = {**globals(), **locals(), **extra, **dynamic}

    if _type in classes:
        if _type == "Indexer":
            constructor = classes[plugin_class]
        else:
            i_class = "I" + _type
            if i_class in classes:
                constructor = classes[i_class]
            else:
                constructor = classes[_type]
    else:
        raise TypeError(f"Could not initialize item, type {_type} not registered in PodClient")
    return constructor


class PluginRun(Item):
    description = """Information about a Plugin container being run by the Pod."""
    properties = Item.properties + [
        "containerId",
        "containerImage",
        "authUrl",
        "authImage",
        "pluginModule",
        "pluginName",
        "status",
        "targetItemId",
        "error",
        "config",
        "progress",
        "webserverPort",
    ]
    edges = Item.edges + ["plugin", "view", "account"]

    def __init__(
        self,
        containerImage: str = None,
        authUrl: str = None,
        authImage: str = None,
        pluginModule: str = None,
        pluginName: str = None,
        status: str = None,
        targetItemId: str = None,
        error: str = None,
        config: str = None,
        progress: float = None,
        webserverPort: int = None,
        containerId: str = None,
        plugin: EdgeList[Plugin] = None,
        view: EdgeList[CVUStoredDefinition] = None,
        account: EdgeList[Account] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        id_ = (
            "".join([random.choice(string.hexdigits) for i in range(32)])
            if targetItemId is None
            else targetItemId
        )
        self.id = id_

        # Properties
        self.containerImage: Optional[str] = containerImage
        self.authUrl: Optional[str] = authUrl
        self.authImage: Optional[str] = authImage
        self.pluginModule: Optional[str] = pluginModule
        self.pluginName: Optional[str] = pluginName
        self.status: Optional[str] = status
        self.targetItemId: Optional[str] = id_
        self.error: Optional[str] = error
        self.config: Optional[str] = config
        self.progress: Optional[float] = progress
        self.webserverPort: Optional[int] = webserverPort
        self.containerId: Optional[str] = containerId

        # Edges
        self.plugin: EdgeList[Plugin] = EdgeList("plugin", "Plugin", plugin)
        self.view: EdgeList[CVUStoredDefinition] = EdgeList("view", "CVUStoredDefinition", view)
        self.account: EdgeList[Account] = EdgeList("account", "Account", account)
