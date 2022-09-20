from datetime import datetime
from pprint import pprint
from typing import Dict, ForwardRef, List, Optional, Union

from pymemri.schema.item import Item, ItemBase, _field_is_edge, get_origin


class Account(Item):
    handle: str = None


class Person(Item):
    name: str = None


class TestItem(Item):
    str_property: str = None
    int_property: int = None
    float_property: float = None
    bool_property: bool = None
    dt_property: datetime = None

    account_edge: List[Account] = []
    union_edge: List[Union[Account, Person]] = []

    # Ignored fields
    _not_property: Optional[str] = None
    _not_edge: List[Item] = []
    not_edge: List[Union[Item, int]] = []
    incorrect_type: Dict[str, int] = None
    incorrect_2: Union[str, int] = None


def test_item():
    item = TestItem(id="1")
    pprint(item.__property_fields__)
    assert len(TestItem.__property_fields__) == 10
    pprint(item.property_dict())


def test_properties():
    item = TestItem(id="1")
    pprint(item.property_dict())


def test_edges():
    item = TestItem(id=1)
    item.add_edge("account_edge", Account())
    assert isinstance(item.account_edge, tuple)
    assert len(item.account_edge) == 1
    assert isinstance(item.account_edge[0], Account)

    print(TestItem.properties, TestItem.edges)

    try:
        item.add_edge("account_edge", TestItem())
    except Exception:
        pass


def test_union_edge():
    # Test for unwanted type coercion
    item = TestItem(id=2)
    item.add_edge("union_edge", Account())
    item.add_edge("union_edge", Person())
    print(item.union_edge)
    assert len(item.union_edge) == 2
    assert isinstance(item.union_edge[0], Account)
    assert isinstance(item.union_edge[1], Person)


def test_schema():
    pprint(TestItem.pod_schema())


test_edges()
