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
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel, PrivateAttr, validator
from pydantic.fields import Field, FieldInfo, ModelField
from pydantic.generics import GenericModel
from pydantic.main import ModelMetaclass

if sys.version_info >= (3, 9, 0):
    from pydantic.main import __dataclass_transform__ as dataclass_transform
else:
    from pydantic.main import dataclass_transform

if TYPE_CHECKING:
    from ..pod.client import PodClient

POD_TYPES: Dict[type, str] = {
    bool: "Bool",
    str: "Text",
    int: "Integer",
    float: "Real",
    datetime: "DateTime",
}

PodType = Union[bool, str, int, float, datetime]

# typing utils for python 3.7
def get_args(type_annotation: Any) -> Any:
    return getattr(type_annotation, "__args__", tuple())


def get_origin(type_annotation: Any) -> Any:
    return getattr(type_annotation, "__origin__", None)


def _field_is_property(field: ModelField) -> bool:
    return field.outer_type_ in POD_TYPES and not field.name.startswith("_")


def _field_is_edge(field: ModelField) -> bool:
    try:
        if field.name.startswith("_") or get_origin(field.outer_type_) != list:
            return False
        args = get_args(field.outer_type_)
        if len(args) != 1:
            return False
        if get_origin(args[0]) == Union:
            target_types = get_args(args[0])
        else:
            target_types = [args[0]]

        return all(issubclass(target_type, ItemBase) for target_type in target_types)
    except Exception:
        return False


TargetType = TypeVar("TargetType")


@dataclass_transform(kw_only_default=True, field_descriptors=(Field, FieldInfo))
class _EdgeMeta(ModelMetaclass):
    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        """
        Metaclass for Edge to ensure an Edge always has a generic argument (ie Edge[Item]).
        If no generic is given to the constructor, it is inferred from type(edge.target)
        """
        target_annotation = cls.__annotations__["target"]
        if isinstance(target_annotation, TypeVar):
            # cls has no generic argument
            generic_val = type(kwds["target"])
            cls = cls[generic_val]  # type: ignore

        return super().__call__(*args, **kwds)


@dataclass_transform(kw_only_default=True, field_descriptors=(Field, FieldInfo))
class _ItemMeta(ModelMetaclass):
    def __new__(mcs, name, bases, namespace, **kwargs) -> Any:
        """
        Metaclass for ItemBase. Adds following class properties:
        - ItemBase.__property_fields__: Dict[str, ModelField]
        - ItemBase.__edge_fields__: Dict[str, ModelField]
        - ItemBase.edges: List[str]
        - ItemBase.properties: List[str]
        """
        res = super().__new__(mcs, name, bases, namespace, **kwargs)

        res.__property_fields__: Dict[str, ModelField] = {
            k: v for k, v in res.__fields__.items() if _field_is_property(v)
        }
        res.__edge_fields__: Dict[str, ModelField] = {
            k: v for k, v in res.__fields__.items() if _field_is_edge(v)
        }

        # For backwards compatibility with old ItemBase
        res.properties = list(res.__property_fields__.keys())
        res.edges = list(res.__edge_fields__.keys())

        return res


class Edge(GenericModel, Generic[TargetType], metaclass=_EdgeMeta, smart_union=True):
    _type: Optional[str]
    source: Any
    target: TargetType
    created: bool = False

    @classmethod
    def get_target_type(cls) -> List[type]:
        return cls.__annotations__["target"]

    @validator("target", pre=True)
    def validate_target(cls, val: Any) -> TargetType:
        target_type = cls.get_target_type()
        if getattr(target_type, "__origin__", None) == Union:
            target_type = target_type.__args__
        if not isinstance(val, target_type):
            raise ValueError(f"value type is not a {cls.__fields__['target']._type_display()}")

        return val

    def __eq__(self, other):
        if (
            isinstance(other, Edge)
            and self._type == other._type
            and self.source == other.source
            and self.target == other.target
        ):
            return True
        return False

    def traverse(self, start: "ItemBase"):
        if start == self.source:
            return self.target
        elif start == self.target:
            return self.source
        else:
            raise ValueError("`start` is not source or target")


ItemType = TypeVar("ItemType", bound="ItemBase")


class ItemBase(BaseModel, metaclass=_ItemMeta):
    __edges__: Dict[str, List[Edge[Any]]] = PrivateAttr()
    _in_pod: bool = PrivateAttr(False)
    _new_edges: List[str] = PrivateAttr(default_factory=list)
    _date_local_modified: Dict[str, datetime] = PrivateAttr(default_factory=dict)
    _original_properties: Dict[str, PodType] = PrivateAttr(default_factory=dict)

    if TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __edge_fields__: ClassVar[Dict[str, ModelField]] = {}
        __property_fields__: ClassVar[Dict[str, ModelField]] = {}
        properties: ClassVar[List[str]] = []
        edges: ClassVar[List[str]] = []

    def __init__(self, **data: Any) -> None:
        # Raise error if edges are in init kwds
        for k, v in data.items():
            if k in self.__edge_fields__ and v:
                raise NotImplementedError("TODO Adding edges on item init is not implemented")

        # TODO populate self.__edges__ with items from data
        self.__edges__ = {k: list() for k in self.__edge_fields__.keys()}
        super().__init__(**data)

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
            # TODO Returning as list might be unclear for user, as appending to this list wont change
            # any edges. Using list for now to conform to type annotations.
            return list(e.traverse(self) for e in super().__getattribute__("__edges__")[__name])
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
            edge = Edge[field.type_](_type=edge_name, source=self, target=target)
            existing_edges = self.__edges__[field.name]
            if edge not in existing_edges:
                existing_edges.append(edge)
                self._new_edges.append(edge)
        else:
            raise ValueError(f"{edge_name} is not an edge on {type(self).__name__}")

    def __str__(self) -> str:
        return f"{type(self).__name__}(#{self.id})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: Any) -> bool:
        # Pydantic does not check for type for eq comparison, only for properties from self.dict()
        if not isinstance(other, type(self)):
            return False
        return super().__eq__(other)

    @classmethod
    def pod_schema(cls) -> List[Dict[str, Any]]:
        """Generates the schema as required by the Pod.

        Returns:
            List[Dict[str, Any]]: List of schema definitions.
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
            target_types = field.type_
            if getattr(target_types, "__origin__", None) == Union:
                target_types = target_types.__args__
            else:
                target_types = [target_types]

            for target_type in target_types:
                edge_schema = {
                    "type": "ItemEdgeSchema",
                    "edgeName": field.name,
                    "sourceType": cls.__name__,
                    "targetType": target_type.__name__,
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

    def create_id_if_not_exists(self):
        if hasattr(self, "id") and getattr(self, "id") is None:
            self.id = uuid.uuid4().hex

    def store(self, client: "PodClient") -> None:
        return client.add_to_store(self)

    def property_dict(
        self, filter_none: bool = True, datetime_to_timestamp: bool = True
    ) -> Dict[str, PodType]:
        """Returns a dict of values of all properties of self

        Args:
            filter_none (bool, optional): Remove `None` value. Defaults to True.
            datetime_to_timestamp (bool, optional): convert datetime values to timestamp in milliseconds. Defaults to True.

        Returns:
            Dict[str, PodType]: Dictionary of all property values
        """
        include = self.__property_fields__.keys()
        res = super().dict(include=include)
        keys_to_remove = list()
        for k, v in res.items():
            if datetime_to_timestamp and isinstance(v, datetime):
                res[k] = round(v.timestamp() * 1000)
            if filter_none and v is None:
                keys_to_remove.append(k)

        for k in keys_to_remove:
            res.pop(k, None)
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
    def from_data(cls: Type[ItemType], *args: List[Any], **kwargs: List[Any]) -> ItemType:
        # TODO
        raise NotImplementedError()

    @classmethod
    def from_json(cls: Type[ItemType], json: Dict[str, Any]) -> ItemType:
        # TODO
        raise NotImplementedError()


Edge.update_forward_refs()


class Item(ItemBase):
    id: Optional[str] = None
    dateCreated: Optional[datetime] = None
    dateModified: Optional[datetime] = None
    dateServerModified: Optional[datetime] = None
    deleted: bool = False
