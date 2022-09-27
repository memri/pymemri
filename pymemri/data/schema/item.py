import sys
import uuid
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    no_type_check,
)

from pydantic import BaseModel, Extra, PrivateAttr, validator
from pydantic.fields import Field, FieldInfo, ModelField
from pydantic.generics import GenericModel
from pydantic.main import ModelMetaclass

from .utils import get_args, get_origin, type_or_union_to_tuple, type_to_str

if sys.version_info >= (3, 9, 0):
    from pydantic.main import __dataclass_transform__ as dataclass_transform
else:
    from pydantic.main import dataclass_transform

if TYPE_CHECKING:
    from ...pod.client import PodClient

SOURCE, TARGET, TYPE, EDGE_TYPE, LABEL, SEQUENCE, ALL_EDGES = (
    "_source",
    "_target",
    "_type",
    "_type",
    "label",
    "sequence",
    "allEdges",
)

POD_TYPES: Dict[type, str] = {
    bool: "Bool",
    str: "Text",
    int: "Integer",
    float: "Real",
    datetime: "DateTime",
}

PodType = Union[bool, str, int, float, datetime]


def _field_is_property(field: ModelField) -> bool:
    return field.outer_type_ in POD_TYPES and not field.name.startswith("_")


def _field_is_edge(field: ModelField) -> bool:
    try:
        if field.name.startswith("_") or get_origin(field.outer_type_) != list:
            return False
        args = get_args(field.outer_type_)
        if args is None or len(args) != 1:
            return False
        return True

    except Exception:
        return False


# @dataclass_transform(kw_only_default=True, field_descriptors=(Field, FieldInfo))
# class _EdgeMeta(ModelMetaclass):
#     def __call__(cls, *args: Any, **kwds: Any) -> Any:
#         """
#         Metaclass for Edge to ensure an Edge always has a generic argument (ie Edge[Item]).
#         If no generic is given to the constructor, it is inferred from type(edge.target)
#         """
#         target_annotation = cls.__annotations__["target"]
#         if isinstance(target_annotation, TypeVar):
#             # cls has no generic argument
#             generic_val = type(kwds["target"])
#             cls = cls[generic_val]  # type: ignore

#         return super().__call__(*args, **kwds)


@dataclass_transform(kw_only_default=True, field_descriptors=(Field, FieldInfo))
class _ItemMeta(ModelMetaclass):
    """
    Metaclass for ItemBase that adds required class and instance properties.

    Note: _itembase_private_attrs is a workaround for hiding private attributes
    generated by pyright/pylance signature. This is only a cosmetic difference,
    private attributres can be defined on a model with `PrivateAttr(default)` value.
    See: https://github.com/pydantic/pydantic/discussions/4563
    """

    _itembase_private_attrs = {
        "_in_pod": PrivateAttr(False),
        "__edges__": PrivateAttr(default_factory=dict),
        "_new_edges": PrivateAttr(default_factory=list),
        "_date_local_modified": PrivateAttr(default_factory=dict),
        "_original_properties": PrivateAttr(default_factory=dict),
    }

    @no_type_check  # noqa C901
    def __new__(mcs, name, bases, namespace, **kwargs) -> Any:  # noqa C901
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        cls.__property_fields__ = {k: v for k, v in cls.__fields__.items() if _field_is_property(v)}
        cls.__edge_fields__ = {k: v for k, v in cls.__fields__.items() if _field_is_edge(v)}

        # For backwards compatibility with old ItemBase
        cls.properties = list(cls.__property_fields__.keys())
        cls.edges = list(cls.__edge_fields__.keys())

        # Add private instance attributes from _itembase_private_attrs
        cls.__private_attributes__ = {**cls.__private_attributes__, **mcs._itembase_private_attrs}
        cls.__slots__ = cls.__slots__ | mcs._itembase_private_attrs.keys()
        return cls


TargetType = TypeVar("TargetType")


class Edge(GenericModel, Generic[TargetType], smart_union=True, copy_on_model_validation=False):
    source: Any
    target: TargetType
    name: str

    def __init__(self, source: Any = None, target: TargetType = None, name: str = None) -> None:
        super().__init__(source=source, target=target, name=name)
        self.source = source
        self.target = target

    @classmethod
    def get_target_types(cls) -> Tuple[type]:
        target_annotation = cls.__annotations__["target"]
        if target_annotation == TargetType:
            return tuple()
        return type_or_union_to_tuple(target_annotation)

    @classmethod
    def get_target_types_as_str(cls) -> Tuple[str]:
        return tuple(type_to_str(t) for t in cls.get_target_types())

    @validator("target", pre=True)
    def validate_target(cls, val: Any) -> TargetType:
        """
        To allow for overwriting schema classes on a different place, validator
        only checks by class name.

        i.e. `Edge[schema.MyItem](target=plugin.MyItem(), ...)` is allowed.
        """
        target_types = cls.get_target_types()
        if len(target_types) == 0:
            # cls has no target type annotations, validator always succeeds
            return val
        if isinstance(val, target_types):
            return val
        ttype_display = cls.__fields__["target"]._type_display()
        raise ValueError(f"target with type `{type(val).__name__}` is not a `{ttype_display}`")

    def __eq__(self, other):
        # Edge source/targets are checked by reference instead of value:
        # edge_1 == edge_2 if they have the same name, and point to the
        # same objects
        if (
            isinstance(other, Edge)
            and self.name == other.name
            and self.source is other.source
            and self.target is other.target
        ):
            return True
        return False

    def traverse(self, start: Any) -> Any:
        if start == self.source:
            return self.target
        elif start == self.target:
            return self.source
        else:
            raise ValueError("`start` is not source or target")


ItemType = TypeVar("ItemType")


class ItemBase(BaseModel, metaclass=_ItemMeta, extra=Extra.forbid):
    if TYPE_CHECKING:
        # class variables populated by the metaclass, defined here to help IDEs only
        __edge_fields__: ClassVar[Dict[str, ModelField]] = {}
        __property_fields__: ClassVar[Dict[str, ModelField]] = {}
        properties: ClassVar[List[str]] = []
        edges: ClassVar[List[str]] = []

    def __init__(self, **data: Dict[str, Any]) -> None:
        if TYPE_CHECKING:
            # instance variables populated by the metaclass, defined here to help IDEs only
            self.__edges__: Dict[str, List[Edge[Any]]] = {}
            self._in_pod: bool = True
            self._new_edges: List[str] = []
            self._date_local_modified: Dict[str, datetime] = {}
            self._original_properties: Dict[str, PodType] = {}

        # Edges are added after super().__init__
        edge_data = {}
        for edge_name in self.__edge_fields__:
            edge_data[edge_name] = data.pop(edge_name, None)

        super().__init__(**data)
        self._init_edges(**edge_data)

    def _init_edges(self, **data: Dict[str, List["ItemBase"]]) -> None:
        self.__edges__ = {k: list() for k in self.__edge_fields__.keys()}
        for edge_name, edge_targets in data.items():
            if edge_targets is not None:
                for edge_target in edge_targets:
                    self.add_edge(edge_name, edge_target)
        self._new_edges = []

    def __setattr__(self, name: str, value: Any) -> None:
        prev_val = getattr(self, name, None)
        super().__setattr__(name, value)
        if name in self.__property_fields__ and value != prev_val:
            self._date_local_modified[name] = datetime.utcnow()
            if name not in self._original_properties:
                self._original_properties[name] = prev_val

    def get_edges(self, name: str) -> List[Edge]:
        return self.__edges__[name]

    def get_all_edges(self) -> List[Edge]:
        return [edge for edge_list in self.__edges__.values() for edge in edge_list]

    def __getattribute__(self, __name: str) -> Any:
        edge_fields = super().__getattribute__("__edge_fields__")
        if __name in edge_fields:
            return [e.traverse(self) for e in super().__getattribute__("__edges__")[__name]]
        return super().__getattribute__(__name)

    def add_edge(self, edge_name: str, target: "ItemBase") -> None:
        """Add a new edge between `self` and `target` with name `edge_name`

        Args:
            edge_name (str): Name of the edge
            target (ItemBase): Target of the edge

        Raises:
            ValueError: Raises error if `edge_name` does not exist on this class
        """
        field = self.__edge_fields__.get(edge_name, None)
        if field is not None:
            edge = Edge[field.type_](name=edge_name, source=self, target=target)
            existing_edges = self.__edges__[field.name]
            if edge not in existing_edges:
                existing_edges.append(edge)
                self._new_edges.append(edge)
        else:
            raise ValueError(f"{edge_name} is not an edge on {type(self).__name__}")

    @classmethod
    def pod_schema(cls) -> List[Dict[str, str]]:
        """Generates the schema as required by the Pod.

        Returns:
            List[Dict[str, str]]: List of schema definitions.
        """
        schema = []
        for field in cls.__property_fields__.values():
            property_schema = {
                "type": "ItemPropertySchema",
                "itemType": cls.__name__,
                "propertyName": field.name,
                "valueType": POD_TYPES[field.type_],
            }
            schema.append(property_schema)

        for field in cls.__edge_fields__.values():
            for target_type in type_or_union_to_tuple(field.type_):
                edge_schema = {
                    "type": "ItemEdgeSchema",
                    "edgeName": field.name,
                    "sourceType": cls.__name__,
                    "targetType": type_to_str(target_type),
                }
                schema.append(edge_schema)
        return schema

    @property
    def _updated_properties(self):
        return set(self._original_properties.keys())

    def reset_local_sync_state(self):
        """
        reset_local_sync_state is called when self is created or updated (optionally via bulk) in the PodClient.
        """
        self._original_properties = dict()
        self._date_local_modified = dict()
        self._in_pod = True

    @staticmethod
    def create_id() -> str:
        return uuid.uuid4().hex

    def create_id_if_not_exists(self):
        if hasattr(self, "id") and getattr(self, "id") is None:
            self.id = self.create_id()

    def store(self, client: "PodClient") -> None:
        return client.add_to_store(self)

    def __str__(self) -> str:
        return f"{type(self).__name__}(#{self.id})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.dict() == other.dict()

    def _iter(
        self,
        *,
        to_dict: bool = False,
        include: set = None,
        exclude: set = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Dict[str, Any]:
        if exclude is None:
            exclude = set(type(self)._itembase_private_attrs)
        else:
            exclude = exclude + set(type(self)._itembase_private_attrs)
        return super()._iter(
            to_dict=to_dict,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    @staticmethod
    def _datetime_to_timestamp(dt: datetime) -> int:
        """Convert datetime to Pod timestamp format"""
        return round(dt.timestamp() * 1000)

    def property_dict(
        self,
        exclude_none: bool = True,
        datetime_to_timestamp: bool = True,
    ) -> Dict[str, PodType]:
        """Returns a dict of values of all properties of self

        Args:
            exclude (bool, optional): Remove `None` values. Defaults to True.
            datetime_to_timestamp (bool, optional): convert datetime values to timestamp in milliseconds. Defaults to True.

        Returns:
            Dict[str, PodType]: Dictionary of all property values
        """
        include = self.__property_fields__.keys()
        res = self.dict(include=include, exclude_none=exclude_none)
        for k, v in res.items():
            if datetime_to_timestamp and isinstance(v, datetime):
                res[k] = self._datetime_to_timestamp(v)
        return res

    def to_json(self) -> Dict[str, PodType]:
        """Returns dict of property values along with the type of self.
        This is the format as expected by the Pod.

        Returns:
            Dict[str, PodType]: Dictionary of all property values
        """
        res = self.property_dict()
        res["type"] = type(self).__name__
        return res

    @classmethod
    def from_data(cls: Type[ItemType], **kwargs: Dict[str, Any]) -> ItemType:
        # TODO remove and use __init__
        return cls(**kwargs)

    @classmethod
    def from_json(
        cls: Type[ItemType], json: Dict[str, Any], properties_only: bool = True
    ) -> ItemType:
        if properties_only:
            json = {k: v for k, v in json.items() if k in cls.properties}
        return cls(**json)


Edge.update_forward_refs()
ItemBase.update_forward_refs()


class Item(ItemBase):
    id: Optional[str] = None
    dateCreated: Optional[datetime] = None
    dateModified: Optional[datetime] = None
    dateServerModified: Optional[datetime] = None
    deleted: bool = False
