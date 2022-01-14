import random, string
from .itembase import ItemBase, Edge, Item
from ._central_schema import *
from .photo import Photo
from .dataset import Dataset


def get_constructor(_type, plugin_class=None, plugin_package=None, extra=None):
    from .photo import Photo
    import pymemri.integrator_registry

    if _type == "Indexer" and plugin_class is not None and hasattr(pymemri.integrator_registry, plugin_class):
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
        "containerImage",
        "authUrl",
        "pluginModule",
        "pluginName",
        "status",
        "targetItemId",
        "error",
        "config",
        "progress",
    ]
    edges = Item.edges + ["plugin", "view", "account"]

    def __init__(
        self,
        containerImage: str = None,
        authUrl: str = None,
        pluginModule: str = None,
        pluginName: str = None,
        status: str = None,
        targetItemId: str = None,
        error: str = None,
        config: str = None,
        progress: float = None,
        plugin: list = None,
        view: list = None,
        account: list = None,
        **kwargs
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
        self.pluginModule: Optional[str] = pluginModule
        self.pluginName: Optional[str] = pluginName
        self.status: Optional[str] = status
        self.targetItemId: Optional[str] = id_
        self.error: Optional[str] = error
        self.config: Optional[str] = config
        self.progress: Optional[float] = progress

        # Edges
        self.plugin: list = plugin if plugin is not None else []
        self.view: list = view if view is not None else []
        self.account: list = account if account is not None else []
