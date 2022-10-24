import typing
from datetime import datetime, timedelta
from time import sleep
from typing import Any, Dict, List, Optional

import pytest
from fastapi import HTTPException
from pydantic import BaseModel

from pymemri.data.schema import PluginRun
from pymemri.plugin.pluginbase import PluginBase
from pymemri.plugin.states import RUN_STARTED
from pymemri.pod.client import PodClient
from pymemri.webserver.models.api_call import CallReq
from pymemri.webserver.public_api import (
    _PUBLIC_API,
    add_to_api,
    call_api,
    get_api,
    register_endpoint,
    remove_from_api,
)

# def teardown_function(function):
#     _PUBLIC_API.clear()


# class DummyPlugin:
#     def __init__(self):
#         self.call_history = list()

#     def function_with_no_args(self):
#         self.call_history.append("function_with_no_args")

#     def function_with_typed_args(self, a: int, b: str, c: float):
#         self.call_history.append(f"function_with_typed_args a {a} b {b} c {c}")

#     def function_with_args_and_return_type(self, a: int, b: str, c: float) -> str:
#         self.call_history.append(f"function_with_args_and_return_type a {a} b {b} c {c}")
#         return "return function_with_args_and_return_type"

#     def function_with_return_type(self) -> str:
#         self.call_history.append("function_with_return_type")
#         return "return function_with_return_type"

#     def function_that_raises(self) -> str:
#         raise RuntimeError("function_that_raises")

#     def function_without_types(self, a, b, c):
#         self.call_history.append("function_without_types")

#     def function_with_some_types(self, a: int, b, c: str):
#         self.call_history.append("function_with_some_types")

#     def function_with_defaults(self, a, b=None):
#         self.call_history.append("function_with_defaults")

#     def function_with_args(self, *args):
#         self.call_history.append("function_with_args")

#     def function_with_kwargs(self, a, **kwargs):
#         self.call_history.append("function_with_kwargs")

#     def function_with_complex_types(self, l: typing.List, t: tuple, s: typing.AnyStr):
#         self.call_history.append("function_with_complex_types")

#     def function_with_boolean(self, flag: bool):
#         self.call_history.append("function_with_boolean")


# def test_invalid_calls():
#     dummy_plugin = DummyPlugin()

#     add_to_api(dummy_plugin.function_with_typed_args)
#     add_to_api(dummy_plugin.function_that_raises)

#     with pytest.raises(HTTPException) as exinfo:
#         # Not enough arguments
#         call_api(CallReq(function="function_with_typed_args", args={"a": 123, "b": "asdf"}))
#     assert "missing 1 required positional argument: 'c'" in exinfo.value.detail

#     with pytest.raises(HTTPException) as exinfo:
#         # Too many args
#         call_api(
#             CallReq(
#                 function="function_with_typed_args",
#                 args={"a": 123, "b": "asdf", "c": 3.14, "d": "wtf"},
#             )
#         )
#     assert "got an unexpected keyword argument 'd'" in exinfo.value.detail

#     with pytest.raises(HTTPException) as exinfo:
#         # not registered function
#         call_api(CallReq(function="unknown", args={"a": 123, "b": "asdf"}))
#     assert "Function unknown is not registered" in exinfo.value.detail

#     with pytest.raises(HTTPException) as exinfo:
#         # function gets into trouble
#         call_api(CallReq(function="function_that_raises", args={}))
#     assert "function_that_raises" in exinfo.value.detail


class MockPlugin(PluginBase):
    def __init__(self):
        super().__init__(
            client=PodClient(), pluginRun=PluginRun(containerImage="", webserverPort=8080)
        )

    def run():
        pass


def test_endpoints_validation():
    with pytest.raises(RuntimeError) as exinfo:

        class Plugin(MockPlugin):
            @register_endpoint(endpoint_name="/v1/api1", method="POST")
            def api1(self, a: int, x, b: list):
                pass

    assert "arguments: ['x'] does not have type annotation" in str(exinfo.value)

    with pytest.raises(RuntimeError) as exinfo:

        class Plugin(MockPlugin):
            @register_endpoint(endpoint_name="/v1/api1", method="POST")
            def api1(self, *args):
                pass

    assert "passed function cannot have *args" in str(exinfo.value)

    with pytest.raises(RuntimeError) as exinfo:

        class Plugin(MockPlugin):
            @register_endpoint(endpoint_name="/v1/api1", method="POST")
            def api1(self, i: int, **kwargs):
                pass

    assert "passed function cannot have **kwargs" in str(exinfo.value)


def test_cannot_register_function_twice_under_the_same_endpoint_and_method():
    class Plugin(MockPlugin):
        @register_endpoint(endpoint_name="/v1/api1", method="POST")
        def api1(self):
            pass

        @register_endpoint(endpoint_name="/v1/api1", method="POST")
        def api2(self, x: int):
            pass

    with pytest.raises(RuntimeError) as exinfo:
        p = Plugin()

    assert "endpoint /v1/api1 with method POST is already registered" in str(exinfo.value)

    # It is possible however to have the same endpoint, but different method
    class Plugin(MockPlugin):
        @register_endpoint(endpoint_name="/v1/api1", method="POST")
        def api1(self):
            pass

        @register_endpoint(endpoint_name="/v1/api1", method="GET")
        def api2(self, x: int):
            pass


def test_cannot_do_nested_decoration():
    with pytest.raises(RuntimeError) as exinfo:

        class Plugin(MockPlugin):
            @register_endpoint(endpoint_name="/v1/api1", method="POST")
            @register_endpoint(endpoint_name="/v1/api1", method="GET")
            def api1(self):
                pass

    assert (
        "register function api1 to ('/v1/api1', 'POST') but is already used in: ('/v1/api1', 'GET')"
        in str(exinfo.value)
    )


def test_can_register_different_endpoints():
    # Declaring a class shall not raise an error
    class Plugin(MockPlugin):
        @register_endpoint("/api1", method="POST")
        def function_with_no_args(self):
            pass

        @register_endpoint("/api2", method="POST")
        def function_with_typed_args(self, a: int, b: str, c: float):
            pass

        @register_endpoint("/api3", method="POST")
        def function_with_args_and_return_type(self, a: int, b: str, c: float) -> str:
            pass

        @register_endpoint("/api4", method="POST")
        def function_with_return_type(self) -> str:
            pass

        @register_endpoint("/api5", method="POST")
        def function_with_defaults(self, a: str, b: datetime = None):
            pass

        @register_endpoint("/api6", method="POST")
        def function_with_complex_types(
            self, l: typing.List[typing.Optional[int]], t: tuple, s: typing.AnyStr
        ):
            pass

        @register_endpoint("/api7", method="POST")
        def function_with_boolean(self, flag: bool):
            pass

    # Instantiating shall not raise either
    _plugin = Plugin()


class PluginRunModel(BaseModel):
    the_port: int

    def build(self) -> PluginRun:
        return PluginRun(webserverPort=self.the_port)


class ReqModel(BaseModel):
    x: int
    # that allows to set bool to null, or discard from the request body completely
    y: Optional[bool]

    # pydantic will try to convert to datetime:
    # int or float, assumed as Unix time,
    # str, following formats work:
    #   YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]]]
    #   int or float as a string (assumed as Unix time)
    d: datetime

    prm: PluginRunModel


# TODO: move to integration tests
# check that call works
# check get /api endpoint
# check get /health endpoint
def test_start_webserver_with_endpoints():
    class Plugin(MockPlugin):
        @register_endpoint(endpoint_name="/v1/api1", method="POST")
        def api1(self, a: list, b: dict, x: int, req: ReqModel, bla: tuple = (1, 2, 3)):

            # # you can call datetime methods without fear
            # _date = req.d.date()

            # # for pymemri custom types we need glue in a form of a Model, that will create
            # # pymemri specific instance:
            # _plugin_run : PluginRun = req.prm.build()

            # # and now use internal plugin method:
            # self._internal_api(_plugin_run)

            print(f"routes: {self._webserver.app.routes}")

        @register_endpoint("/v1/gonna_raise", method="POST")
        def function_that_raises(self) -> str:
            raise RuntimeError("function_that_raises")

    # p = Plugin()

    # p.setup()

    # print("webserver should run")
    # sleep(600)
