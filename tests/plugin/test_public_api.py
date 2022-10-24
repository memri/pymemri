import typing
from datetime import datetime
from time import sleep
from typing import Optional

import pytest
import requests
from pydantic import BaseModel

from pymemri.data.schema import PluginRun
from pymemri.plugin.pluginbase import PluginBase
from pymemri.plugin.states import RUN_INITIALIZED
from pymemri.pod.client import PodClient
from pymemri.webserver.public_api import register_endpoint


class MockPlugin(PluginBase):
    def __init__(self):
        super().__init__(
            client=PodClient(), pluginRun=PluginRun(containerImage="", webserverPort=8080)
        )

        self.base_endpoint = "http://127.0.0.1:8080"

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


# Integration tests
def _wait_for_webapi(endpoint, attempts=30):
    while attempts > 0:
        try:
            requests.get(f"{endpoint}/v1/api")
            return
        except Exception as e:
            print(f"waiting for server {e}")
            attempts -= 1
            sleep(1)

    raise RuntimeError(f"Cannot connect to plugin's {endpoint} webapi")


def test_webserver_reports_base_api():
    # Base class defines v1/health, and v1/api endpoints
    class Plugin(MockPlugin):
        pass

    p = Plugin()
    p.setup()

    _wait_for_webapi(p.base_endpoint)

    resp = requests.get(f"{p.base_endpoint}/v1/api")

    assert resp.status_code == 200
    assert {
        "/v1/api": {"method": "GET", "args": {}},
        "/v1/health": {"method": "GET", "args": {}},
    } == resp.json()

    resp = requests.get(f"{p.base_endpoint}/v1/health")
    assert resp.status_code == 200
    assert resp.json() == RUN_INITIALIZED

    # Shuting down takes some time due to the listeners
    p.teardown()


def test_different_types_in_endpoint():
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

    class Plugin(MockPlugin):
        @register_endpoint(endpoint_name="/v1/echo", method="POST")
        def echo(
            self,
            a: typing.List[typing.AnyStr],
            b: dict,
            x: int,
            req: ReqModel,
            t: tuple = (1, 2, 3),
        ):
            return {"a": a, "b": b, "x": x, "req": req, "t": t}

    p = Plugin()
    p.setup()

    _wait_for_webapi(p.base_endpoint)

    # Valid call
    req = {
        "a": ["string", "string"],
        "b": {},
        "req": {"x": 0, "y": True, "d": "2022-10-24T19:38:09.718Z"},
        "t": [1, 2, 3],
    }

    resp = requests.post(f"{p.base_endpoint}/v1/echo?x=13", json=req)
    assert resp.status_code == 200
    assert {
        "a": ["string", "string"],
        "b": {},
        "req": {"x": 0, "y": True, "d": "2022-10-24T19:38:09.718000+00:00"},
        "t": [1, 2, 3],
        "x": 13,
    } == resp.json()

    # Valid call, removed optional 'y' field
    req = {
        "a": ["string", "string"],
        "b": {},
        "req": {
            "x": 0,
            # "y": True,
            "d": "2022-10-24T19:38:09.718Z",
        },
        "t": [1, 2, 3],
    }

    resp = requests.post(f"{p.base_endpoint}/v1/echo?x=13", json=req)
    assert resp.status_code == 200
    assert {
        "a": ["string", "string"],
        "b": {},
        "req": {"x": 0, "y": None, "d": "2022-10-24T19:38:09.718000+00:00"},
        "t": [1, 2, 3],
        "x": 13,
    } == resp.json()

    # Invalid method 'get'
    resp = requests.get(f"{p.base_endpoint}/v1/echo")
    assert resp.status_code == 405

    # Invalid request, missing required 'b'
    req = {
        "a": ["string", "string"],
        "req": {"x": 0, "y": True, "d": "2022-10-24T19:38:09.718Z"},
        "t": [1, 2, 3],
    }

    resp = requests.post(f"{p.base_endpoint}/v1/echo?x=13", json=req)

    assert resp.status_code == 422
    assert "field required" in resp.json()["detail"][0]["msg"]

    # Invalid request, violating schema, by introducing non-string element in the List[AnyStr]
    req = {
        "a": ["string", "string", None],
        "b": {},
        "req": {"x": 0, "y": True, "d": "2022-10-24T19:38:09.718Z"},
        "t": [1, 2, 3],
    }

    resp = requests.post(f"{p.base_endpoint}/v1/echo?x=13", json=req)

    assert resp.status_code == 422
    assert "none is not an allowed value" in resp.json()["detail"][0]["msg"]

    # Shuting down takes some time due to the listeners
    p.teardown()
