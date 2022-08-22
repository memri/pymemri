import pytest
from pymemri.pod.client import PodClient
from pymemri.data.schema import Dataset, DatasetEntry, Account, Person, Message, EmailMessage, CategoricalLabel
from pymemri.data.itembase import Edge
import pandas as pd

@pytest.fixture
def client():
    client = PodClient()
    client.add_to_schema(Account, Person, Message, EmailMessage, Dataset, DatasetEntry, CategoricalLabel)
    return client


def create_dummy_dataset(client, num_items):
    dataset = Dataset(name="example-dataset")

    num_items = 10
    messages = []
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
        edges.extend([
            Edge(dataset, entry, "entry"),
            Edge(entry, msg, "data"),
            Edge(msg, account, "sender"),
            Edge(entry, label, "label"),
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
    columns = ["data.content", "data.sender.handle", "label.labelValue"]
    dataframe = dataset.to("pd", columns=columns)
    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == num_items
    assert all(dataframe.columns == ["id"] + columns)
    assert dataframe["data.content"][0] == "content_0"
    assert dataframe["data.content"][1] == "email content_1"
    assert dataframe['data.sender.handle'][0] == "account_0"
