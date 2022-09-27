from collections import UserList
from typing import Any, ForwardRef, Tuple, Union


# typing utils for python 3.7
def get_args(type_annotation: Any) -> Any:
    return getattr(type_annotation, "__args__", tuple())


def get_origin(type_annotation: Any) -> Any:
    return getattr(type_annotation, "__origin__", None)


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
    if get_origin(field.type_) == Union:
        new_args = tuple(
            arg._evaluate(globalns=None, localns=schema, recursive_guard=set())
            for arg in get_args(field.type_)
            if isinstance(arg, ForwardRef)
        )
        field.type_.__args__ = new_args


def resolve_forward_refs(schema):
    for schema_cls in list(schema.values()):
        schema_cls.update_forward_refs(**schema)
        for field in schema_cls.__edge_fields__.values():
            update_union_forward_refs(field, schema)
