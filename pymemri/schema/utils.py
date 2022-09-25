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


class EdgeTargets(UserList):
    """
    Separate implementation for List for ItemBase error handling.
    Required if users attempt to insert or remove edges through an edge property: List[TargetType] on an item.

    Tuple is not used here to conform to type checking (returned type should be list)
    """

    _modify_error_msg = "Cannot modify edges by modifying edge targets. use Item.add_edge instead"

    def append(self, item: Any) -> None:
        raise RuntimeError(self._modify_error_msg)

    def extend(self, other: Any) -> None:
        raise RuntimeError(self._modify_error_msg)

    def pop(self, i: int = ...) -> Any:
        raise RuntimeError(self._modify_error_msg)

    def __add__(self, other) -> None:
        raise RuntimeError(self._modify_error_msg)

    def __iadd__(self: Any, other: any) -> Any:
        raise RuntimeError(self._modify_error_msg)

    def __setitem__(self, i: int, item: Any) -> None:
        raise RuntimeError(self._modify_error_msg)

    def insert(self, i: int, item: Any) -> None:
        raise RuntimeError(self._modify_error_msg)
