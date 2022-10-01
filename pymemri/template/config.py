import inspect
import json
import os
from pathlib import Path
from typing import List

from fastcore.script import Param, call_parse
from loguru import logger

from ..plugin.pluginbase import get_plugin_cls
from ..pod.client import PodClient

ALLOWED_TYPES = [int, str, float, bool]


def get_params(cls):
    params = inspect.signature(cls.__init__).parameters
    return {k: v for k, v in list(params.items()) if k not in {"self", "args", "kwargs"}}


def identifier_to_displayname(identifier: str) -> str:
    return identifier.replace("_", " ").title()


def get_param_config(name, dtype, is_optional, default):
    return {
        "name": name,
        "display": identifier_to_displayname(name),
        "data_type": dtype,
        "type": "textbox",
        "default": default,
        "optional": is_optional,
    }


def create_config(plugin_cls: type) -> List[dict]:
    """
    Returns a declarative plugin configuration, inferred from the `__init__` method signature of `plugin_cls`.
    This function is used internally by the `create_plugin_config` CLI. For general use, use the CLI instead.

    Arguments that start with `_`, untyped arguments or arguments that are not in `ALLOWED_TYPES` are skipped.

    Args:
        plugin_cls (type): A plugin class, inherited from PluginBase.

    Returns:
        List[dict]: A declarative configuration definition as list of dictionaries.
    """
    config = list()
    for param_name, param in get_params(plugin_cls).items():
        if param_name.startswith("_"):
            continue
        if param.annotation == inspect._empty:
            logger.info(f"Skipping unannotated parameter `{param_name}`")
            continue
        if param.annotation not in ALLOWED_TYPES:
            logger.info(f"Skipping parameter with unknown type: `{param_name}: {param.annotation}`")
            continue
        is_optional = param.default != inspect._empty
        dtype = PodClient.TYPE_TO_SCHEMA[param.annotation]
        default = param.default if is_optional else None
        param_config = get_param_config(param_name, dtype, is_optional, default)
        config.append(param_config)
    return config


@call_parse
def create_plugin_config(
    metadata: Param("metadata.json of the plugin", str) = "./metadata.json",
    tgt_file: Param("Filename of config file", str) = "config.json",
    schema_file: Param("Filename of exported plugin schema", str) = "schema.json",
):
    """
    Creates a plugin configuration definition from the arguments of your plugin class.

    Configuration arguments are inferred from the arguments of your plugin `__init__` method.
    Arguments that start with `_`, untyped arguments or arguments that are not in `ALLOWED_TYPES` are skipped.
    All generated fields are "textbox" by default, in the future our front-end will support more
    types of fields.
    Args:
        metadata (Param, optional): Location of the "metadata.json" file,
            Defaults to "./metadata.json"
        tgt_file (Param, optional): File the config definition is saved to.
            Defaults to "config.json".
    """
    if metadata is None:
        if os.path.exists("./metadata.json"):
            metadata = "./metadata.json"
        else:
            print("Define a metadata file with --metadata <filename>")
            return
    with open(metadata, "r") as f:
        metadata = json.load(f)

    plugin_module = metadata["pluginModule"]
    plugin_name = metadata["pluginName"]

    try:
        plugin_cls = get_plugin_cls(plugin_module, plugin_name)
    except Exception as e:
        logger.error(e)
        return
    config = create_config(plugin_cls)

    with open(tgt_file, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Config saved to {Path(tgt_file)}")

    plugin_schema = plugin_cls.get_schema()
    with open(schema_file, "w") as f:
        json.dump(plugin_schema, f, indent=2)
