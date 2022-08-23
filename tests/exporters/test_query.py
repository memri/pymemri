import random

import pandas as pd
import pytest
from pymemri.data.itembase import Edge
from pymemri.data.schema import Account, CategoricalPrediction, Message, Person
from pymemri.exporters.exporters import Query
from pymemri.pod.client import PodClient


@pytest.fixture
def client():
    client = PodClient()
    client.add_to_schema(Account, Person, Message, CategoricalPrediction)
    return client


def create_dummy_dataset(client: PodClient, num_items=10):
    messages = []
    items = []
    edges = []
    for i in range(num_items):
        msg = Message(content=f"content_{i}", service="my_service")
        account = Account(handle=f"account_{i}")
        person = Person(firstName=f"firstname_{i}")
        label = CategoricalPrediction(value=f"label_{i}")
        items.extend([msg, account, person, label])
        edges.extend(
            [
                Edge(msg, account, "sender"),
                Edge(msg, label, "label"),
                Edge(account, person, "owner"),
            ]
        )
        messages.append(msg)

    # Dataset is not perfect, drop some random edges
    edges = random.sample(edges, int(len(edges) * 0.8))

    client.bulk_action(create_items=items, create_edges=edges)


def test_query(client: PodClient):
    num_items = 10
    create_dummy_dataset(client, num_items)
    messages = client.search({"type": "Message", "service": "my_service"})

    q = Query("content", "label.value", "sender.owner.firstName", "sender.handle", "wrong_property")
    result = q.execute(client, messages)

    assert all(len(vals) == len(result["content"]) for vals in result.values())
    assert len(result["content"]) == num_items

    valid_props = ["label.value", "sender.owner.firstName", "sender.handle"]
    for i in range(num_items):
        row = [result[prop][i] for prop in valid_props]
        row_idx = [val[-1] for val in row if val is not None]
        assert len(set(row_idx)) <= 1

    assert all(val is None for val in result["wrong_property"])

    result_pandas = q.execute(client, messages, dtype="pandas")
    assert isinstance(result_pandas, pd.DataFrame)
