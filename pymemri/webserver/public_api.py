from inspect import getfullargspec

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from pymemri.webserver.models.api_call import CallReq

router = APIRouter()

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

    arg_annotations_count = (
        len(args.annotations) if "return" not in args.annotations else len(args.annotations) - 1
    )
    args_count = len(args.args) if "self" not in args.args else len(args.args) - 1

    if args_count != arg_annotations_count:
        raise RuntimeError(f"passed function lacks of type annotations")

    _PUBLIC_API[func_name] = func


def remove_from_api(func_name: str):
    if func_name in _PUBLIC_API:
        del _PUBLIC_API[func_name]


# TODO: remove
# conclusion: decorator cannot be used, because it does not capture "self", it captures unbounded methods

# SELF = None
# PUBLIC_API = dict()

# # class PublicApi:
# #     def __init__(self, fun_self, fun):
# #         print(f"init deco, args {fun_self}")
# #         functools.update_wrapper(self, fun(fun_self))

# #         # self._func_name = func.__name__
# #         # PUBLIC_API[self._func_name] = func


# #     def __call__(self, *args, **kwargs):
# #         # print(f"calling decorated {self._func_name}, args {args}, kwargs {kwargs}")

# #         # return PUBLIC_API[self._func_name](args[0])
# #         pass

# #     def deregister(self):
# #         del PUBLIC_API[self._func_name]

# def PublicApi(func):
#     @functools.wraps(func)
#     def _decorator(self, *args, **kwargs):
#         print("calling decorated")
#         return func(self, *args, **kwargs)

#     return _decorator

# def PublicApiCtx(cls):


# @PublicApiCtx
# class Plug:
#     def __init__(self):
#         # SELF = self
#         pass

#     @PublicApi
#     def func1(self, x: int) -> str:
#         return str(x*x)

# def handle_post_call(req):
#     return PUBLIC_API[req["function"]](SELF, **req["args"])


# def test_decorating():

#     plug = Plug()

#     # # print("type hints", get_type_hints(plug.func1))

#     print("using function normally")
#     plug.func1(12)

#     print("using as webserver callback")
#     res = handle_post_call({"function": "func1", "args": {"x": 5}})

#     print(f"callback res {res}")

#     res = handle_post_call({"function": "func1", "args": {"y": 5}})
#     # print("deregistering")
#     # plug.func1.deregister()


#     # print("still can use function normally")
#     # plug.func1(12)

#     # print("but cannot use via public api")
#     # res = handle_post_call({"function": "func1", "args": {"x": 5}})
