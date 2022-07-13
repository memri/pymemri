from .itembase import Item, EdgeList


class Trigger(Item):
    properties = Item.properties + ["triggerOn", "action"]
    pass