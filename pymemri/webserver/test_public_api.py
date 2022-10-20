import typing

import pytest
from fastapi import HTTPException

from pymemri.webserver.models.api_call import CallReq
from pymemri.webserver.public_api import (
    _PUBLIC_API,
    add_to_api,
    call_api,
    get_api,
    remove_from_api,
)


def teardown_function(function):
    _PUBLIC_API.clear()


class DummyPlugin:
    def __init__(self):
        self.call_history = list()

    def function_with_no_args(self):
        self.call_history.append("function_with_no_args")

    def function_with_typed_args(self, a: int, b: str, c: float):
        self.call_history.append(f"function_with_typed_args a {a} b {b} c {c}")

    def function_with_args_and_return_type(self, a: int, b: str, c: float) -> str:
        self.call_history.append(f"function_with_args_and_return_type a {a} b {b} c {c}")
        return "return function_with_args_and_return_type"

    def function_with_return_type(self) -> str:
        self.call_history.append("function_with_return_type")
        return "return function_with_return_type"

    def function_that_raises(self) -> str:
        raise RuntimeError("function_that_raises")

    def function_without_types(self, a, b, c):
        self.call_history.append("function_without_types")

    def function_with_some_types(self, a: int, b, c: str):
        self.call_history.append("function_with_some_types")

    def function_with_defaults(self, a, b=None):
        self.call_history.append("function_with_defaults")

    def function_with_args(self, *args):
        self.call_history.append("function_with_args")

    def function_with_kwargs(self, a, **kwargs):
        self.call_history.append("function_with_kwargs")

    def function_with_complex_types(self, l: typing.List, t: tuple, s: typing.AnyStr):
        self.call_history.append("function_with_complex_types")


def test_can_register_different_functions():
    dummy_plugin = DummyPlugin()
    # Empty dict at the beginning
    assert not get_api()

    add_to_api(dummy_plugin.function_with_no_args)
    add_to_api(dummy_plugin.function_with_typed_args)
    add_to_api(dummy_plugin.function_with_args_and_return_type)
    add_to_api(dummy_plugin.function_with_return_type)

    add_to_api(dummy_plugin.function_with_return_type, "aliasing_function")

    with pytest.raises(RuntimeError) as exinfo:
        add_to_api(dummy_plugin.function_without_types)
    assert "lacks of type annotations" in str(exinfo.value)

    with pytest.raises(RuntimeError) as exinfo:
        add_to_api(dummy_plugin.function_with_some_types)
    assert "lacks of type annotations" in str(exinfo.value)

    with pytest.raises(RuntimeError) as exinfo:
        add_to_api(dummy_plugin.function_with_defaults)
    assert "cannot have default arguments" in str(exinfo.value)

    with pytest.raises(RuntimeError) as exinfo:
        add_to_api(dummy_plugin.function_with_args)
    assert "cannot have *args" in str(exinfo.value)

    with pytest.raises(RuntimeError) as exinfo:
        add_to_api(dummy_plugin.function_with_kwargs)
    assert "cannot have **kwargs" in str(exinfo.value)

    assert {
        "function_with_no_args": {},
        "function_with_typed_args": {"a": "int", "b": "str", "c": "float"},
        "function_with_args_and_return_type": {
            "return": "str",
            "a": "int",
            "b": "str",
            "c": "float",
        },
        "function_with_return_type": {"return": "str"},
        "aliasing_function": {"return": "str"},
    } == get_api()


def test_can_register_function_with_complex_arguments():
    dummy_plugin = DummyPlugin()
    add_to_api(dummy_plugin.function_with_complex_types)
    assert {
        "function_with_complex_types": {"l": "typing.List", "t": "tuple", "s": "AnyStr"}
    } == get_api()


def test_can_call_different_functions():
    dummy_plugin = DummyPlugin()
    add_to_api(dummy_plugin.function_with_no_args)
    add_to_api(dummy_plugin.function_with_typed_args)
    add_to_api(dummy_plugin.function_with_args_and_return_type)
    add_to_api(dummy_plugin.function_with_return_type)
    add_to_api(dummy_plugin.function_with_return_type, "aliasing_function")

    assert [] == dummy_plugin.call_history

    call_api(CallReq(function="function_with_no_args", args={}))
    call_api(CallReq(function="function_with_typed_args", args={"a": 123, "b": "asdf", "c": 2.4}))
    res = call_api(
        CallReq(
            function="function_with_args_and_return_type", args={"a": 222, "b": "str", "c": 3.14}
        )
    )

    assert res == "return function_with_args_and_return_type"

    call_api(
        CallReq(
            function="function_with_return_type",
            args={},
        )
    )
    call_api(CallReq(function="aliasing_function", args={}))

    assert [
        "function_with_no_args",
        "function_with_typed_args a 123 b asdf c 2.4",
        "function_with_args_and_return_type a 222 b str c 3.14",
        "function_with_return_type",
        # note aliasing_function redirects to valid one
        "function_with_return_type",
    ] == dummy_plugin.call_history


def test_invalid_calls():
    dummy_plugin = DummyPlugin()

    add_to_api(dummy_plugin.function_with_typed_args)
    add_to_api(dummy_plugin.function_that_raises)

    with pytest.raises(HTTPException) as exinfo:
        # Not enough arguments
        call_api(CallReq(function="function_with_typed_args", args={"a": 123, "b": "asdf"}))
    assert "missing 1 required positional argument: 'c'" in exinfo.value.detail

    with pytest.raises(HTTPException) as exinfo:
        # Too many args
        call_api(
            CallReq(
                function="function_with_typed_args",
                args={"a": 123, "b": "asdf", "c": 3.14, "d": "wtf"},
            )
        )
    assert "got an unexpected keyword argument 'd'" in exinfo.value.detail

    with pytest.raises(HTTPException) as exinfo:
        # not registered function
        call_api(CallReq(function="unknown", args={"a": 123, "b": "asdf"}))
    assert "Function unknown is not registered" in exinfo.value.detail

    with pytest.raises(HTTPException) as exinfo:
        # function gets into trouble
        call_api(CallReq(function="function_that_raises", args={}))
    assert "function_that_raises" in exinfo.value.detail


def test_can_deregister_functions():
    dummy_plugin = DummyPlugin()

    add_to_api(dummy_plugin.function_with_no_args)
    add_to_api(dummy_plugin.function_with_typed_args)
    add_to_api(dummy_plugin.function_with_args_and_return_type)
    add_to_api(dummy_plugin.function_with_return_type)
    add_to_api(dummy_plugin.function_with_return_type, "aliasing_function")

    assert {
        "function_with_no_args": {},
        "function_with_typed_args": {"a": "int", "b": "str", "c": "float"},
        "function_with_args_and_return_type": {
            "return": "str",
            "a": "int",
            "b": "str",
            "c": "float",
        },
        "function_with_return_type": {"return": "str"},
        "aliasing_function": {"return": "str"},
    } == get_api()

    remove_from_api("function_with_no_args")
    remove_from_api("function_with_typed_args")
    remove_from_api("function_with_args_and_return_type")
    remove_from_api("function_with_return_type")
    remove_from_api("aliasing_function")

    assert {} == get_api()

    # No exception when removing twice
    remove_from_api("aliasing_function")
    # No exception when removing unknown
    remove_from_api("unknown")

    # Can add again
    add_to_api(dummy_plugin.function_with_no_args)
    assert {
        "function_with_no_args": {},
    } == get_api()


def test_cannot_register_twice_function_with_the_same_name():
    def function(a: int) -> str:
        pass

    add_to_api(function)

    with pytest.raises(RuntimeError) as exinfo:
        add_to_api(function)

    assert "already registered" in str(exinfo.value)

    add_to_api(function, "different_name")
