# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/itembase.ipynb (unless otherwise specified).

__all__ = ['ALL_EDGES', 'DB', 'parse_base_item_json', 'Edge', 'ItemBase', 'Item']

# Cell
# hide
from ..imports import *

ALL_EDGES = "allEdges"
SOURCE, TARGET, TYPE, EDGE_TYPE, LABEL, SEQUENCE = "_source", "_target", "_type", "_type", "label", "sequence"

# Cell
# hide
class DB():
    def __init__(self):
        self.nodes = dict()

    def add(self, node):
        id = node.id
        if id in self.nodes:
            print(f"Error trying to add node, but node with with id: {id} is already in database")
        self.nodes[id] = node

    def get(self, id):
        res = self.nodes.get(id, None)
        return res

    def contains(node):
        id = node.get_property("id")
        return id in self.nodes

    def create(self, node):
        existing = self.get(node.properties.get("id", None))

        if existing is not None:
            if not existing._expanded:
                existing.edges = node.edges
                existing._expanded = node.edges is not None
            return existing
        else:
            self.add(node)
            return node

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

class ItemBase():
    """Provides a base class for all items. All items in the schema inherit from this class, and it provides some
    basic functionality for consistency and to enable easier usage."""
    global_db = DB()

    def __init__(self, id=None):
        self.id=id
        self.add_to_db(self)

    @classmethod
    def add_to_db(cls, node):
        existing = cls.global_db.get(node.id)
        if existing is None and node.id is not None:
            cls.global_db.add(node)

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
            for e in self.get_all_edges():
                e.update(api)

    def exists(self, api):
        res = api.search_by_fields({"id": self.id})
        if res is None: return False
        return len(res) == 1

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
    properties = ["dateAccessed", "dateCreated", "dateModified", "deleted", "externalId", "itemDescription",
                  "starred", "version", "id", "importJson", "pluginClass"]
    edges = ["changelog", "label", "genericAttribute", "measure", "sharedWith"]
    def __init__(self, **kwargs):
        super().__init__(kwargs.get("id"))
        for p in self.properties:
            if p == "id":
                continue
            setattr(self, p, kwargs.get(p, None))

        for e in self.edges:
            setattr(self, e, kwargs.get(e, []))

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
    def remove_prefix(s, prefix="~"):
        return s[1:] if s[0] == "`" else s

    @classmethod
    def from_json(cls, json):
        kwargs = Item.parse_json(cls, json)
        res = cls(**kwargs)
        for e in res.get_all_edges(): e.source = res
        return res