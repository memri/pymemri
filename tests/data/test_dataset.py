import pytest
from pymemri.pod.client import PodClient
from pymemri.data.schema import Dataset, DatasetEntry, Account, Person, Message, Label
from pymemri.data.itembase import Edge
import pandas as pd

@pytest.fixture
def client():
    client = PodClient()
    client.add_to_schema(Account, Person, Message, Dataset, DatasetEntry, Label)
    return client


def create_dummy_dataset(client, num_items):
    dataset = Dataset(name="example-dataset")

    num_items = 10
    messages = []
    items = [dataset]
    edges = []
    for i in range(num_items):
        entry = DatasetEntry()
        msg = Message(content=f"content_{i}", service="my_service")
        account = Account(handle=f"account_{i}")
        person = Person(firstName=f"firstname_{i}")
        label = Label(name=f"label_{i}")
        items.extend([entry, msg, account, person, label])
        edges.extend([
            Edge(dataset, entry, "entry"),
            Edge(entry, msg, "data"),
            Edge(msg, account, "sender"),
            Edge(entry, label, "annotation"),
            Edge(account, person, "owner")
        ])
        messages.append(msg)

    client.bulk_action(
        create_items=items,
        create_edges=edges
    )


def test_dataset(client):
    num_items = 10
    create_dummy_dataset(client, num_items)
    dataset = client.get_dataset("example-dataset")
    columns = ["data.content", "data.sender.handle", "annotation.name"]
    dataframe = dataset.to("pd", columns=columns)
    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == num_items
    assert all(dataframe.columns == ["id"] + columns)
