import sys
from collections import UserList
from typing import Any, Dict, ForwardRef, Tuple, Union

if sys.version_info >= (3, 9, 0):
    from typing import get_args, get_origin

    def evaluate_type(type_: Any, localns) -> Any:
        return type_._evaluate(globalns=None, localns=localns, recursive_guard=set())

else:

    def get_args(type_annotation: Any) -> Any:
        return getattr(type_annotation, "__args__", tuple())

    def get_origin(type_annotation: Any) -> Any:
        return getattr(type_annotation, "__origin__", None)

    def evaluate_type(type_: Any, localns) -> Any:
        return type_._evaluate(globalns=None, localns=localns)


def type_to_str(_type: type) -> str:
    """Returns string representation of `_type`, ForwardRef is supported."""
    if isinstance(_type, type):
        return _type.__name__
    elif isinstance(_type, ForwardRef):
        return _type.__forward_arg__


def type_or_union_to_tuple(_type: type) -> Tuple[type]:
    """converts Union[TypeA, TypeB] to (TypeA, TypeB)

    If _type is not a union, return (_type,)
    """
    if get_origin(_type) == Union:
        return tuple(get_args(_type))
    return (_type,)


def update_union_forward_refs(field, schema):
    # Standard pydantic resolver does not handle Union[ForwardRef(A), ForwardRef(B)] -> Union[A, B]
    # TODO log as issue with Pydantic
    if get_origin(field.type_) == Union:
        new_args = tuple(
            evaluate_type(arg, localns=schema)
            for arg in get_args(field.type_)
            if isinstance(arg, ForwardRef)
        )
        field.type_.__args__ = new_args


def resolve_forward_refs(schema: Dict[str, type]):
    """
    Resolve forward refs for all classes in schema.values()
    """
    for schema_cls in list(schema.values()):
        schema_cls.update_forward_refs(**schema)
        for field in schema_cls.__edge_fields__.values():
            update_union_forward_refs(field, schema)
