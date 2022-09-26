from datetime import datetime
from optparse import Option
from typing import List, Optional, Union

import pytest
from pydantic import ValidationError

from pymemri.data.schema import Account, Item, Person, get_schema
from pymemri.pod.client import PodClient


class MyItem(Item):
    str_property: Optional[str] = None
    int_property: Optional[int] = None
    float_property: Optional[float] = None
    bool_property: Optional[bool] = None
    dt_property: Optional[datetime] = None

    account_edge: List[Account] = []
    union_edge: List[Union[Account, Person]] = []


def test_item_init():
    item = Account(handle="my_account")
    item2 = Account.from_json({"handle": "my_account"})
    item3 = Account.from_json(item.to_json())
    assert item == item2 == item3

    with pytest.raises(ValidationError):
        item = Account(handle="my_account", not_a_property=False)


def test_init_with_edges():
    accounts = [Account(handle="1"), Account(handle="2")]
    item = MyItem(str_property="test", account_edge=accounts)
    assert item.property_dict() == {"deleted": False, "str_property": "test"}
    assert len(item.account_edge) == len(item.__edges__["account_edge"]) == 2


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
        "deleted": False,
    }
    assert property_dict == correct_properties


def test_private_attrs():
    item = MyItem()
    assert item._in_pod == False
    item._in_pod = True
    assert item._in_pod == True


def test_add_edge():
    item = MyItem()
    person = Person()
    account = Account()

    item.add_edge("account_edge", account)

    with pytest.raises(ValidationError):
        item.add_edge("account_edge", person)

    assert len(item.account_edge) == 1


def test_get_edge():
    person = Person(id="0")
    account = Account(id="1")

    item = MyItem()
    item.add_edge("account_edge", account)
    item.add_edge("union_edge", person)

    assert len(item.get_edges("account_edge")) == 1
    assert len(item.get_edges("union_edge")) == 1
    assert len(item.get_all_edges()) == 2

    targets = [edge.target for edge in item.get_all_edges()]
    assert person in targets and account in targets


def test_central_schema_to_pod():
    client = PodClient()
    for k, v in get_schema().items():
        assert client.add_to_schema(v), f"Could not add {k} to schema"

    assert len(client.api.search({"type": "ItemPropertySchema"}))
    assert len(client.api.search({"type": "ItemEdgeSchema"}))


def test_create_and_read_item():
    # TODO clean up this test
    client = PodClient()
    assert client.add_to_schema(Account, MyItem)

    item = MyItem(str_property="test", int_property=1)
    account = Account(handle="friend")
    item.add_edge("account_edge", account)

    assert client.create(item)
    assert client.create(account)

    item_2 = client.get(item.id)
    assert len(item_2.account_edge) == 1
    assert item_2.account_edge[0].handle == "friend"
    assert item_2.str_property == "test"
    assert item_2.int_property == 1
