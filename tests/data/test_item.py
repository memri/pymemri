from datetime import datetime
from typing import List, Optional, Union

import pytest
from pydantic import ValidationError

from pymemri.data.schema import (
    Account,
    CategoricalPrediction,
    Edge,
    Item,
    Person,
    RSSEntry,
    get_schema,
)
from pymemri.data.schema.schema import SchemaMeta
from pymemri.pod.client import PodClient


class MyItem(Item):
    str_property: Optional[str] = None
    int_property: Optional[int] = None
    float_property: Optional[float] = None
    bool_property: Optional[bool] = None
    dt_property: Optional[datetime] = None

    accountEdge: List[Account] = []
    unionEdge: List[Union[Account, Person]] = []


def test_definition():
    assert MyItem.properties == Item.properties + [
        "str_property",
        "int_property",
        "float_property",
        "bool_property",
        "dt_property",
    ]
    assert MyItem.edges == Item.edges + ["accountEdge", "unionEdge"]
    # + 1 for union edge
    pod_schema = MyItem.pod_schema()

    assert len(pod_schema.edges.keys()) == len(MyItem.edges)
    assert len(pod_schema.properties) == len(MyItem.properties)


def test_item_init():
    item = Account(handle="my_account")
    item2 = Account.from_json({"handle": "my_account"})
    item3 = Account.from_json(item.to_json())
    assert item == item2 == item3

    with pytest.raises(ValidationError):
        item = Account(handle="my_account", not_a_property=False)


def test_init_with_edges():
    accounts = [Account(handle="1"), Account(handle="2")]
    item = MyItem(str_property="test", accountEdge=accounts)
    assert item.property_dict() == {"str_property": "test"}
    assert len(item.accountEdge) == len(item.__edges__["accountEdge"]) == 2


def test_property_dict():
    dt = datetime.now()
    item = MyItem(bool_property=0, int_property=1, str_property=2, float_property=3, dt_property=dt)
    property_dict = item.property_dict()

    correct_properties = {
        "int_property": 1,
        "str_property": "2",
        "float_property": 3.0,
        "bool_property": False,
        "dt_property": round(dt.timestamp() * 1000),
    }
    assert property_dict == correct_properties


def test_private_attrs():
    item = MyItem()
    assert item._in_pod == False
    item._in_pod = True
    assert item._in_pod == True
    assert "_in_pod" not in item.to_json()


def test_validate_edge():
    _ = Edge(MyItem(), Account(), "test")
    _ = Edge[Account](MyItem(), Account(), "test")

    with pytest.raises(ValidationError):
        _ = Edge(1, Account(), "test")
    with pytest.raises(ValidationError):
        _ = Edge(Account(), 1, "test")
    with pytest.raises(ValidationError):
        _ = Edge[Account](Account(), Person(), "test")


def test_add_edge():
    item = MyItem()
    person = Person()
    account = Account()

    item.add_edge("accountEdge", account)

    with pytest.raises(ValidationError):
        item.add_edge("accountEdge", person)

    assert len(item.accountEdge) == 1


def test_union_edge():
    item = MyItem()
    account = Account(handle="test1")
    person = Person(firstName="test2")

    item.add_edge("unionEdge", account)
    item.add_edge("unionEdge", person)

    assert len(item.unionEdge) == 2
    assert item.unionEdge[0].handle == "test1"
    assert item.unionEdge[1].firstName == "test2"


def test_get_edge():
    person = Person(id="0")
    account = Account(id="1")

    item = MyItem()
    item.add_edge("accountEdge", account)
    item.add_edge("unionEdge", person)

    assert len(item.get_edges("accountEdge")) == 1
    assert len(item.get_edges("unionEdge")) == 1
    assert len(item.get_all_edges()) == 2

    targets = [edge.target for edge in item.get_all_edges()]
    assert person in targets and account in targets


def test_central_schema_to_pod():
    # Central Schema is already set by POD
    client = PodClient()
    client.api.search({"type": "Message"})


def test_create_and_read_item():
    # TODO clean up this test
    client = PodClient()
    assert client.add_to_schema(
        SchemaMeta(name="test_dataset", url="example.com", version="0.1"),
        Account,
        MyItem,
    )

    item = MyItem(str_property="test", int_property=1)
    account = Account(handle="friend")
    item.add_edge("accountEdge", account)

    assert client.create(item)
    assert client.create(account)

    item_2 = client.get(item.id)
    assert len(item_2.accountEdge) == 1
    assert item_2.accountEdge[0].handle == "friend"
    assert item_2.str_property == "test"
    assert item_2.int_property == 1


def test_item_json():
    item = RSSEntry(
        title="test",
    )
    edge = item.add_edge("label", CategoricalPrediction(value="test"))

    item_dict = item.dict()
    assert item_dict["label"] != None
