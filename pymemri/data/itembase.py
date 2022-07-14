# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/itembase.ipynb (unless otherwise specified).

__all__ = ['ALL_EDGES', 'Edge', 'check_target_type', 'EdgeList', 'T', 'ItemBase', 'Item']

# Cell
# hide
from typing import Optional, Dict, List, Generic, TypeVar, Tuple, Union, Iterable, ForwardRef
from ..imports import *
from datetime import datetime
import uuid

ALL_EDGES = "allEdges"
SOURCE, TARGET, TYPE, EDGE_TYPE, LABEL, SEQUENCE = "_source", "_target", "_type", "_type", "label", "sequence"

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
T = TypeVar('T')

def check_target_type(fn):
    """
    Decorator to perform type check the target type of the first argument, or list of arguments.
    """
    def _check_type_wrapper(self, arg):
        if isinstance(arg, Iterable):
            for item in arg:
                if type(item.target).__name__ != self.target_type:
                    raise TypeError("Attempted to insert edge with invalid target type")
        elif isinstance(arg, Edge):
            if type(arg.target).__name__ != self.target_type:
                raise TypeError("Attempted to insert edge with invalid target type")
        else:
            raise TypeError("Attempted to insert edge with invalid type")
        return fn(self, arg)
    return _check_type_wrapper

class EdgeList(list, Generic[T]):
    def __init__(
        self,
        name: str,
        target_type: Union[type, str, ForwardRef],
        data: List[Edge] = None,
    ) -> None:
        super().__init__()
        self.name = name

        if isinstance(target_type, type):
            target_type = target_type.__name__
        elif isinstance(target_type, ForwardRef):
            target_type = target_type.__forward_arg__
        self.target_type = target_type

        if data is not None:
            self.extend(data)

    @property
    def targets(self) -> List["Item"]:
        return [edge.target for edge in self]

    # Wrap all append, extend and add methods
    @check_target_type
    def append(self, item: Edge) -> None:
        return super().append(item)

    @check_target_type
    def extend(self, other: Iterable[Edge]) -> None:
        return super().extend(other)

    @check_target_type
    def __add__(self, other: Iterable[Edge]) -> "EdgeList":
        return super().__add__(other)

    @check_target_type
    def __iadd__(self, other: Iterable[Edge]) -> "EdgeList":
        return super().__iadd__(other)

    def __setitem__(self, i:  int, item: Edge) -> None:
        if isinstance(item, Edge):
            if type(item.target).__name__ != self.target_type:
                raise TypeError("Attempted to insert edge with invalid target type")
        else:
            raise TypeError("Attempted to insert edge with invalid type")
        return super().__setitem__(i, item)

    def insert(self, i: int, item: Edge) -> None:
        if isinstance(item, Edge):
            if type(item.target).__name__ != self.target_type:
                raise TypeError("Attempted to insert edge with invalid target type")
        else:
            raise TypeError("Attempted to insert edge with invalid type")
        return super().insert(i, item)


# Cell
# hide
class ItemBase:
    """Provides a base class for all items.
    All items in the schema inherit from this class, and it provides some
    basic functionality for consistency and to enable easier usage."""

    properties: List[str] = list()
    edges: List[str] = list()

    def __init__(self, id: str = None):
        self._date_local_modified = dict()
        self._in_pod: bool = False
        self._new_edges = list()
        self._original_properties = dict()

        self.id: Optional[str] = id

    def __setattr__(self, name, value):
        prev_val = getattr(self, name, None)
        super(ItemBase, self).__setattr__(name, value)

        if name in self.properties and value != prev_val:
            self._date_local_modified[name] = datetime.utcnow()
            if name not in self._original_properties:
                self._original_properties[name] = prev_val

    @property
    def _updated_properties(self):
        return set(self._original_properties.keys())

    def __getattribute__(self, name):
        val = object.__getattribute__(self, name)
        if name in object.__getattribute__(self, "edges"):
            if isinstance(val, Edge):
                return val.traverse(start=self)
            if isinstance(val, EdgeList):
                return [edge.traverse(start=self) for edge in val]
        return val

    def reset_local_sync_state(self):
        """
        reset_local_sync_state is called when self is created or updated (optionally via bulk) in the PodClient.
        """
        self._original_properties = dict()
        self._date_local_modified = dict()
        self._in_pod = True

    def add_edge(self, name, val):
        """Creates an edge of type name and makes it point to val"""
        if name not in self.edges:
            raise NameError(f"object {self} does not have edge with name {name}")

        existing = object.__getattribute__(self, name)
        edge = Edge(self, val, name, created=True)
        if edge not in existing:
            existing.append(edge)
            self._new_edges.append(edge)

    def is_expanded(self):
        """returns whether the node is expanded. An expanded node retrieved nodes that are
        *directly* connected to it
        from the pod, and stored their values via edges in the object."""
        return len(self.get_all_edges()) > 0

    def get_edges(self, name):
        return object.__getattribute__(self, name)

    def get_all_edges(self):
        return [
            e
            for attr in self.__dict__.values()
            if self.attr_is_edge(attr)
            for e in attr
        ]

    def get_all_edge_names(self):
        return [k for k, v in self.__dict__.items() if self.attr_is_edge(v)]

    def get_property_names(self):
        return [k for k, v in self.__dict__.items() if not type(v) == list]

    @staticmethod
    def attr_is_edge(attr):
        return isinstance(attr, list) and len(attr) > 0 and isinstance(attr[0], Edge)

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

    def create_id_if_not_exists(self):
        if self.id is None:
            self.id = uuid.uuid4().hex

    def store(self, client: "PodClient"):
        return client.add_to_store(self)

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

# Cell
class Item(ItemBase):
    """Item is the baseclass for all of the data classes."""

    properties = [
        "dateCreated",
        "dateModified",
        "dateServerModified",
        "deleted",
        "externalId",
        "itemDescription",
        "starred",
        "version",
        "id",
        "importJson",
        "pluginClass",
        "isMock",
    ]
    edges = ["label"]

    DATE_PROPERTIES = ['dateCreated', 'dateModified', 'dateServerModified']

    def __init__(
        self,
        dateCreated: datetime = None,
        dateModified: datetime = None,
        dateServerModified: datetime = None,
        deleted: bool = None,
        externalId: str = None,
        itemDescription: str = None,
        starred: bool = None,
        version: str = None,
        id: str = None,
        importJson: str = None,
        pluginClass: str = None,
        isMock: bool = None,
        label: EdgeList["CategoricalLabel"] = None,
    ):
        super().__init__(id)

        # Properties
        self.dateCreated: Optional[str] = dateCreated
        self.dateModified: Optional[str] = dateModified
        self.dateServerModified: Optional[str] = dateServerModified
        self.deleted: Optional[str] = deleted
        self.externalId: Optional[str] = externalId
        self.itemDescription: Optional[str] = itemDescription
        self.starred: Optional[str] = starred
        self.version: Optional[str] = version
        self.importJson: Optional[str] = importJson
        self.pluginClass: Optional[str] = pluginClass
        self.isMock: Optional[bool] = isMock

        # Edges
        self.label: EdgeList["CategoricalLabel"] = EdgeList(
            "label", "CategoricalLabel", label
        )

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
    def get_edge_types(cls) -> Dict[str, Tuple[str, str]]:
        """
        Infer the types of all edges in cls as tuple (source_type, target_type)
        """
        mro = cls.mro()
        tgt_types = dict()
        for basecls in reversed(mro[:mro.index(ItemBase)]):
            tgt_types.update(basecls.__init__.__annotations__)
        tgt_types = {k: v for k, v in tgt_types.items() if k in cls.edges}

        res = dict()
        for k, v in tgt_types.items():
            if hasattr(v, "__args__") and len(v.__args__):
                v = v.__args__[0]
                if isinstance(v, type):
                    v = v.__name__
                elif isinstance(v, ForwardRef):
                    v = v.__forward_arg__
            else:
                v = "Any"
            res[k] = (cls.__name__, v)
        return res

    @classmethod
    def remove_prefix(s, prefix="~"):
        return s[1:] if s[0] == "`" else s

    @classmethod
    def from_json(cls, json):
        kwargs = Item.parse_json(cls, json)

        property_types = cls.get_property_types(dates=True)
        for k, v in kwargs.items():
            if v is not None and property_types[k] == datetime:
                # Datetime in pod is in milliseconds
                kwargs[k] = datetime.fromtimestamp(v / 1000.)
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
                if isinstance(v, datetime):
                    # Save datetimes in milliseconds
                    v = int(v.timestamp() * 1000)
                res[k] = v
        res["type"] = self._get_schema_type()
        return res
