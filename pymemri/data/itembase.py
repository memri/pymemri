# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/itembase.ipynb (unless otherwise specified).

__all__ = ['ALL_EDGES', 'parse_base_item_json', 'Edge', 'ItemBase', 'Item']

# Cell
# hide
from typing import Optional, Dict
from ..imports import *

ALL_EDGES = "allEdges"
SOURCE, TARGET, TYPE, EDGE_TYPE, LABEL, SEQUENCE = "_source", "_target", "_type", "_type", "label", "sequence"

# Cell
# hide
def parse_base_item_json(json):
    id = json.get("id", None)
    dateAccessed = json.get("dateAccessed", None)
    dateCreated = json.get("dateCreated", None)
    dateModified = json.get("dateModified", None)
    deleted = json.get("deleted", None)
    externalId = json.get("externalId", None)
    itemDescription = json.get("itemDescription", None)
    starred = json.get("starred", None)
    version = json.get("version", None)

    return id, dateAccessed, dateCreated, dateModified, deleted, externalId, itemDescription, starred, version, None, None

# Cell
class Edge():
    """Edges makes a link between two `ItemBase` Items. You won't use this class a lot in practice, as edges are
    abstracted away for normal users. When items are retrieved from the database, the edges are parsed automatically.
    When you add an edge between to items within pymemri, you will often use `ItemBase.add_edge`"""
    def __init__(self, source, target, _type, label=None, sequence=None, created=False, reverse=True):
        self.source   = source
        self.target   = target
        self._type    = _type
        self.label    = label
        self.sequence = sequence
        self.created  = created
        self.reverse  = reverse

    @classmethod
    def from_json(cls, json):
        from .schema import get_constructor
        # we only set the target here
        _type = json[EDGE_TYPE]
        json_target = json[TARGET]
        target_type = json_target["_type"]
        plugin_class = json_target.get("pluginClass", None)
        target_constructor = get_constructor(target_type, plugin_class)
        target = target_constructor.from_json(json_target)
        return cls(source=None, target=target, _type=_type)

    def __repr__(self):
        return f"{self.source} --{self._type}-> {self.target}"

    def update(self, api):
        if self.created:
            api.create_edges([self])

    def __eq__(self, other):
        return self.source is other.source and self.target is other.target \
         and self._type == other._type and self.reverse == other.reverse and self.created == other.created \
         and self.label == other.label

    def traverse(self, start):
        """We can traverse an edge starting from the source to the target or vice versa. In practice we often call
        item.some_edge_type, which calls item.traverse(edgetype), which in turn calls this function."""
        if start == self.source:
            return self.target
        elif start == self.target:
            return self.source
        else:
            raise ValueError

# Cell
# hide
class ItemBase():
    """Provides a base class for all items.
    All items in the schema inherit from this class, and it provides some
    basic functionality for consistency and to enable easier usage."""

    def __init__(self, id: str = None):
        self.id: Optional[str] = id

    def __getattribute__(self, name):
        val = object.__getattribute__(self, name)
        if isinstance(val, Edge):
            edge = val
            return edge.traverse(start=self)
        if isinstance(val, list) and len(val) > 0 and isinstance(val[0], Edge):
            edges = val
            return [edge.traverse(start=self) for edge in edges]
        else:
            return val

    def add_edge(self, name, val):
        """Creates an edge of type name and makes it point to val"""
        val = Edge(self, val, name, created=True)
        if name not in self.__dict__:
            raise NameError(f"object {self} does not have edge with name {name}")
        existing = object.__getattribute__(self, name)
        if val not in existing:
            res = existing + [val]
            self.__setattr__(name, res)

    def is_expanded(self):
        """returns whether the node is expanded. An expanded node retrieved nodes that are
        *directly* connected to it
        from the pod, and stored their values via edges in the object."""
        return len(self.get_all_edges()) > 0

    def get_edges(self, name):
        return object.__getattribute__(self, name)

    def get_all_edges(self):
        return [e for attr in self.__dict__.values() if self.attr_is_edge(attr) for e in attr]

    def get_all_edge_names(self):
        return [k for k,v in self.__dict__.items() if self.attr_is_edge(v)]

    def get_property_names(self):
        return [k for k, v in self.__dict__.items() if not type(v) == list]

    @staticmethod
    def attr_is_edge(attr):
        return isinstance(attr, list) and len(attr)>0 and isinstance(attr[0], Edge)

    def update(self, api, edges=True, create_if_not_exists=True, skip_nodes=False):

        if not self.exists(api):
            print(f"creating {self}")
            api.create(self)
        else:
            print(f"updating {self}")
            api.update_item(self)

        if edges:
            api.create_edges(self.get_all_edges())

    def exists(self, api):
        return api.exists(self.id) if self.id else None

#     def expand(self, api):
#         """Expands a node (retrieves all directly connected nodes ands adds to object)."""
#         self._expanded = True
#         res = api.get(self.id, expanded=True)
#         for edge_name in res.get_all_edge_names():
#             edges = res.get_edges(edge_name)
#             for e in edges:
#                 e.source = self
#             self.__setattr__(edge_name, edges)

#         # self.edges = res.edges
#         return self

    def __repr__(self):
        id = self.id
        _type = self.__class__.__name__
        return f"{_type} (#{id})"

    @classmethod
    def from_data(cls, *args, **kwargs):
        edges = dict()
        new_kwargs = dict()
        for k, v in kwargs.items():
            if isinstance(v, ItemBase):
                edge = Edge(None, v, k)
                edges[k] = edge
                new_kwargs[k] = edge
            else:
                new_kwargs[k] = v

        res = cls(*args, **new_kwargs)

        for v in edges.values():
            v.source = res
        return res

#     def inherit_funcs(self, other):
#         """This function can be used to inherit new functionalities from a subclass. This is a patch to solve
#         the fact that python does provide extensions of classes that are defined in a different file that are
#         dynamic enough for our use case."""
#         assert issubclass(other, self.__class__)
#         self.__class__ = other

# Cell
class Item(ItemBase):
    """Item is the baseclass for all of the data classes."""

    properties = [
        "dateAccessed",
        "dateCreated",
        "dateModified",
        "deleted",
        "externalId",
        "itemDescription",
        "starred",
        "version",
        "id",
        "importJson",
        "pluginClass",
    ]
    edges = ["changelog", "label", "genericAttribute", "measure", "sharedWith"]

    DATE_PROPERTIES = ['dateCreated', 'dateModified', 'dateServerModified']

    def __init__(
        self,
        dateAccessed: str = None,
        dateCreated: str = None,
        dateModified: str = None,
        deleted: bool = None,
        externalId: str = None,
        itemDescription: str = None,
        starred: bool = None,
        version: str = None,
        id: str = None,
        importJson: str = None,
        pluginClass: str = None,
        changelog: list = None,
        label: list = None,
        genericAttribute: list = None,
        measure: list = None,
        sharedWith: list = None
    ):
        super().__init__(id)

        # Properties
        self.dateAccessed: Optional[str] = dateAccessed
        self.dateCreated: Optional[str] = dateCreated
        self.dateModified: Optional[str] = dateModified
        self.deleted: Optional[str] = deleted
        self.externalId: Optional[str] = externalId
        self.itemDescription: Optional[str] = itemDescription
        self.starred: Optional[str] = starred
        self.version: Optional[str] = version
        self.importJson: Optional[str] = importJson
        self.pluginClass: Optional[str] = pluginClass

        # Edges
        self.changelog: list = changelog if changelog is not None else []
        self.label: list = label if label is not None else []
        self.genericAttribute: list = genericAttribute if genericAttribute is not None else []
        self.measure: list = measure if measure is not None else []
        self.sharedWith: list = sharedWith if sharedWith is not None else []

    @classmethod
    def parse_json(self, cls, json):
        property_kwargs = Item.parse_properties(cls, json)
        edge_kwargs = Item.parse_edges(cls, json)
        return {**property_kwargs, **edge_kwargs}

    @classmethod
    def parse_properties(self, cls, json):
        return {p: json.get(p, None) for p in cls.properties}

    @classmethod
    def parse_edges(self, cls, json):
        all_edges = json.get(ALL_EDGES, None)
        edge_kwargs = dict()
        reverse_edges = [f"~{e}" for e in cls.edges]
        if all_edges is not None:
            for edge_json in all_edges:
                edge = Edge.from_json(edge_json)
                if edge.type in self.edges + reverse_edges:
                    edge_name = self.remove_prefix(edge.type)
                    if edge_name in edge_kwargs:
                        edge_kwargs[edge_name] += [edge]
                    else:
                        edge_kwargs[edge_name] = [edge]
        return edge_kwargs

    @classmethod
    def get_property_types(cls, dates=False) -> Dict[str, type]:
        """
        Infer the property types of all properties in cls.
        Raises ValueError if type anotations for properties are missing in the cls init.
        """
        mro = cls.mro()
        property_types = dict()
        for basecls in reversed(mro[:mro.index(ItemBase)]):
            property_types.update(basecls.__init__.__annotations__)
        property_types = {k: v for k, v in property_types.items() if k in cls.properties}

        if not set(property_types.keys()) == set(cls.properties):
            raise ValueError(f"Item {cls.__name__} has missing property annotations.")

        res = dict()
        for k, v in property_types.items():
            if k[:1] != '_' and k != "private" and not (isinstance(v, list)) \
                            and v is not None and (not (dates == False and k in cls.DATE_PROPERTIES)):
                res[k] = v
        return res

    @classmethod
    def remove_prefix(s, prefix="~"):
        return s[1:] if s[0] == "`" else s

    @classmethod
    def from_json(cls, json):
        kwargs = Item.parse_json(cls, json)
        res = cls(**kwargs)
        for e in res.get_all_edges():
            e.source = res
        return res

    def _get_schema_type(self):
        for cls in self.__class__.mro():
            if cls.__name__ != "ItemBase":
                return cls.__name__

    def to_json(self, dates=True):
        res = dict()
        private = getattr(self, "private", [])
        for k, v in self.__dict__.items():
            if k[:1] != '_' and k != "private" and k not in private and not (isinstance(v, list)) \
                            and v is not None and (not (dates == False and k in self.DATE_PROPERTIES)):
                res[k] = v
        res["type"] = self._get_schema_type()
        return res
