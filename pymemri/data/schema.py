from .itembase import ItemBase, Edge, Item
from .central_schema import *


class PluginItem(Item):
    properties = Item.properties + ["containerImage"]
    edges = Item.edges
    def __init__(self, containerImage=None, **kwargs):
        super().__init__(**kwargs)
        self.containerImage = containerImage


def get_constructor(_type, plugin_class=None, plugin_package=None, extra=None):
    from pymemri.data.photo import Photo
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
    if _type == "Plugin":
        return PluginItem

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
