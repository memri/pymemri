import inspect

import pytest

from pymemri.data import _central_schema
from pymemri.pod.client import PodClient


@pytest.fixture
def central_schema():
    return {
        k: v
        for k, v in inspect.getmembers(_central_schema)
        if inspect.isclass(v) and v.__module__ == "pymemri.data._central_schema"
    }


def test_add_to_schema(central_schema):
    client = PodClient()
    for k, v in central_schema.items():
        assert client.add_to_schema(v), f"Could not add {k} to schema"
