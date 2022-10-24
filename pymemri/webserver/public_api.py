import typing
from inspect import getfullargspec

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from pymemri.webserver.models.api_call import CallReq

router = APIRouter()

ENDPOINT_METADATA = "__endpoint_metadata__"


def register_endpoint(endpoint_name: str, method: str):
    """Registers `fn` under endpoint `endpoint_name` into the webserver as public API.
    The `method` parameter specifies HTTP operation: GET, POST, DELETE, etc
    The `fn` needs to pass the validation, for example cannot contain *args, **kwargs,
    all arguments needs to have type annotation."""

    def _add_endpoint_metadata_attr(fn):
        args = getfullargspec(fn)

        # *args makes fastapi crash upon calling the handler
        if args.varargs:
            raise RuntimeError(f"passed function cannot have *args")

        # Allowing **kwargs:
        # - leaks python detail to the API
        # - is treated as string in query parameter: "{"key": value, ...}", instead of {"key": value}
        if args.varkw:
            raise RuntimeError(f"passed function cannot have **kwargs")

        # Requiring typing enforces api clarity
        missing_annotations = []
        for arg in args.args:
            if arg != "self" and arg not in args.annotations:
                missing_annotations.append(arg)

        if missing_annotations:
            raise RuntimeError(f"arguments: {missing_annotations} does not have type annotation")

        metadata = (endpoint_name, method)

        if hasattr(fn, ENDPOINT_METADATA):
            raise RuntimeError(
                f"Trying to register function {fn.__name__} to {metadata} but is already used in: {fn.__endpoint_metadata__}"
            )

        fn.__endpoint_metadata__ = metadata
        return fn

    return _add_endpoint_metadata_attr


_PUBLIC_API = dict()


@router.get("/api", response_class=JSONResponse)
def get_api():
    """Returns exposed functions of the plugin"""

    def get_friendly_annotation_name(kv):
        """Annotation can be done by class, like: int, list, str
        or by alias from typing module, like List, Sequence, Tuple.
        """
        k, v = kv
        if hasattr(v, "__name__"):
            # For classes, use __name__ that returns
            # more concise value
            return (k, v.__name__)
        else:
            # The typing aliases do not provide __name__ attribute, so use
            # __repr__ implementation.
            return (k, str(v))

    resp = {
        func_name: dict(map(get_friendly_annotation_name, getfullargspec(func).annotations.items()))
        for (func_name, func) in _PUBLIC_API.items()
    }
    return resp


@router.post("/api/call", response_class=JSONResponse)
def call_api(req: CallReq):
    """Calls specified `function` with `args`. Returns `function` result."""
    try:
        return _PUBLIC_API[req.function](**req.args)
    except TypeError as ex:
        raise HTTPException(status_code=400, detail=f"Invalid function call {ex}")
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Function {req.function} is not registered")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Error during function call: {ex}")


def add_to_api(func, func_name=None):
    if func_name is None:
        func_name = func.__name__

    if func_name in _PUBLIC_API:
        raise RuntimeError(f"function with name {func_name} is already registered")

    args = getfullargspec(func)

    # TODO: we can relax those constrains in the future
    if args.varargs:
        raise RuntimeError(f"passed function cannot have *args")

    if args.varkw:
        raise RuntimeError(f"passed function cannot have **kwargs")

    if args.defaults:
        raise RuntimeError(f"passed function cannot have default arguments")

    missing_annotations = []
    for arg in args.args:
        if arg != "self" and arg not in args.annotations:
            missing_annotations.append(arg)

    if missing_annotations:
        raise RuntimeError(f"arguments: {missing_annotations} does not have type annotation")

    _PUBLIC_API[func_name] = func


def remove_from_api(func_name: str):
    if func_name in _PUBLIC_API:
        del _PUBLIC_API[func_name]
