import itertools

import pandas as pd
import pytest

from pymemri.data.schema import (
    Account,
    CategoricalLabel,
    Dataset,
    DatasetEntry,
    EmailMessage,
    Message,
    Person,
)
from pymemri.pod.client import PodClient


@pytest.fixture
def client():
    client = PodClient()
    client.add_to_schema(
        {"name": "test_dataset", "url": "example.com", "version": "0.1"},
        Account,
        Person,
        Message,
        EmailMessage,
        Dataset,
        DatasetEntry,
        CategoricalLabel,
    )
    return client


def test_new_schema(client):
    pass


def create_dummy_dataset(client, num_items):
    dataset = Dataset(name="example-dataset")

    items = [dataset]
    edges = []
    for i in range(num_items):
        entry = DatasetEntry()
        if i % 2 == 0:
            msg = Message(content=f"content_{i}", service="my_service")
        else:
            msg = EmailMessage(content=f"email content_{i}", service="my_email_provider")
        account = Account(handle=f"account_{i}")
        person = Person(firstName=f"firstname_{i}")
        label = CategoricalLabel(labelValue=f"label_{i}")
        items.extend([entry, msg, account, person, label])

        dataset.add_edge("entry", entry)
        entry.add_edge("annotation", label)
        entry.add_edge("data", msg)
        msg.add_edge("sender", account)
        account.add_edge("owner", person)

    edges = list(
        itertools.chain(
            dataset.get_all_edges(),
            entry.get_all_edges(),
            msg.get_all_edges(),
            account.get_all_edges(),
        )
    )

    client.bulk_action(create_items=items, create_edges=edges)


def test_dataset(client):
    num_items = 10
    create_dummy_dataset(client, num_items)
    dataset = client.get_dataset("example-dataset")
    columns = ["data.content", "data.sender.handle", "annotation.labelValue"]
    dataframe = dataset.to("pd", columns=columns)
    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == num_items
    assert all(dataframe.columns == ["id"] + columns)
    assert dataframe["data.content"][0] == "content_0"
    assert dataframe["data.content"][1] == "email content_1"
