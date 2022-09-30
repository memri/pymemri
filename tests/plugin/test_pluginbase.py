import os
import subprocess
import sys
import time

import pytest

from pymemri.data.schema import Account, PluginRun
from pymemri.examples.example_plugin import ExamplePlugin
from pymemri.plugin import states
from pymemri.plugin.pluginbase import PluginBase, run_plugin_from_run_id
from pymemri.pod.client import PodClient
from pymemri.test_utils import get_project_root


@pytest.fixture
def example_metadata_path():
    return get_project_root() / "pymemri" / "examples" / "example_plugin.json"


@pytest.fixture
def client():
    subprocess.run(["store_keys", "--replace", "False"])
    return PodClient.from_local_keys()


def test_plugin_schema():
    example_schema = ExamplePlugin.get_schema()
    assert isinstance(example_schema, list)
    assert len(example_schema)


def test_run_from_id(client):
    sys.path.append(get_project_root() / "examples")

    run = PluginRun(
        containerImage="",
        pluginModule="pymemri.examples.example_plugin",
        pluginName="ExamplePlugin",
        status="not started",
    )
    account = Account(identifier="login", secret="password")
    run.add_edge("account", account)

    assert client.create(run)
    assert client.create(account)
    assert client.create_edge(run.get_edges("account")[0])

    run_plugin_from_run_id(run.id, client)

    client.reset_local_db()
    run = client.get(run.id)
    assert run.status == states.RUN_COMPLETED


def test_example_metadata(example_metadata_path):
    assert os.path.exists(example_metadata_path)


def test_run_plugin_cli(example_metadata_path):
    result = subprocess.run(
        ["run_plugin", "--metadata", example_metadata_path], stdout=subprocess.PIPE
    )
    success_message = result.stdout.splitlines()[-1]
    assert success_message == b"Run success!"


@pytest.mark.skip(reason="TODO build example plugin in CI")
def test_simulate_run_cli(client, example_metadata_path):
    subprocess.run(
        ["simulate_run_plugin_from_frontend", "--metadata", example_metadata_path],
        stdout=subprocess.PIPE,
    )

    t0 = time.time()
    while time.time() - t0 < 60:
        # TODO check if container has started first
        time.sleep(3)
        run = client.search_last_added("PluginRun")
        if run.status == states.RUN_COMPLETED:
            break
        assert run.status == states.RUN_STARTED

    run = client.search_last_added("PluginRun")
    assert run.status == states.RUN_COMPLETED
