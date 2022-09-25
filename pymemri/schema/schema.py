import inspect
from typing import Dict
from uuid import uuid4

from pydantic import validator

from ._central_schema import *  # noqa: F405, type: ignore
from .item import Item, ItemType  # noqa: F405, type: ignore


def get_schema() -> Dict[str, ItemType]:
    return {k: v for k, v in globals().items() if inspect.isclass(v) and issubclass(v, Item)}


def get_schema_cls(cls_name: str, extra: Dict[str, ItemType] = None) -> ItemType:
    """Returns the schema model for `cls_name` if it is in central schema or extra.

    If both central schema and extra contain a class with the same `__name__`, extra
    has the priority.

    Args:
        cls_name (str): Name of the schema model to return the class for
        extra (Dict[str, type], optional): _description_. Defaults to None.

    Raises:
        TypeError: `cls_name` is not a known schema model.

    Returns:
        ItemType: subclass of ItemBase
    """
    if extra and cls_name in extra:
        return extra[cls_name]

    pymemri_schema = get_schema()
    if cls_name in pymemri_schema:
        return pymemri_schema[cls_name]
    else:
        raise TypeError(f"{cls_name} is not a known schema model")


class PluginRun(PluginRun):
    @validator("id", always=True)
    def validate_has_run_id(cls, value, values, **kwargs):
        if value is None:
            value = cls.create_id()
        return value

    @validator("targetItemId", always=True)
    def validate_id_is_targetItemId(cls, value, values, **kwargs):
        uid = values.get("id")
        if value is None:
            value = uid

        if value != uid:
            raise ValueError("targetItemId should match id")

        return value


# Leave at bottom of schema.py
# Pydantic needs to resolve forward refs for all schemas
for schema_cls in get_schema().values():
    schema_cls.update_forward_refs(localns=locals())
