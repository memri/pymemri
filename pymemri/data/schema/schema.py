import inspect
from typing import Any, Dict

from pydantic import validator
from pydantic.fields import Field

from ._central_schema import *  # noqa
from .dataset import Dataset  # noqa
from .photo import Photo  # noqa
from .utils import resolve_forward_refs


def get_schema() -> Dict[str, type]:
    return {k: v for k, v in globals().items() if inspect.isclass(v) and issubclass(v, Item)}


def get_schema_cls(cls_name: str, extra: Optional[Dict[str, type]] = None) -> type:
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
    @validator("id", always=True, allow_reuse=True)
    def validate_has_run_id(
        cls, value: Any, values: Dict[str, Any], **kwargs: Dict[str, Any]
    ) -> Any:
        if value is None:
            value = cls.create_id()
        return value

    @validator("targetItemId", always=True, allow_reuse=True)
    def validate_id_is_targetItemId(
        cls, value: Any, values: Dict[str, Any], **kwargs: Dict[str, Any]
    ) -> Any:
        uid = values.get("id")
        if value is None:
            value = uid

        if value != uid:
            raise ValueError("targetItemId should match id")

        return value


# Required for typechecking on forward refs in schema
# Leave at bottom of schema.py
resolve_forward_refs(get_schema())
