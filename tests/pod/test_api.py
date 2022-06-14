import pytest
import random
import uuid

from pymemri.pod.api import PodAPI, PodError
from pymemri.pod.client import PodClient
from pymemri.data.schema import Account, Person, Message
from pymemri.data.itembase import Edge


@pytest.fixture(scope="module")
def api():
    """
    Setup pod account with some dummy data, return API with account keys.
    """
    client = PodClient()
    client.add_to_schema(Account, Person, Message)

    client.api.create_item({
        "type": "ItemEdgeSchema",
        "edgeName": "sender",
        "sourceType": "Message",
        "targetType": "Account",
    })
    client.api.create_item({
        "type": "ItemEdgeSchema",
        "edgeName": "owner",
        "sourceType": "Account",
        "targetType": "Person",
    })

    # Create dummy data
    person = Person(displayName="Alice")
    accounts = [
        Account(displayName="Alice", service="whatsapp"),
        Account(displayName="Alice", service="instagram"),
        Account(displayName="Alice", service="gmail"),
    ]

    message = Message(service="whatsapp", subject="Hello")
    edges = [Edge(account, person, "owner") for account in accounts]
    edges += [Edge(message, accounts[0], "sender")]
    client.bulk_action(create_items=accounts + [person, message], create_edges=edges)

    # Create data for search
    search_accounts = [Account(displayName=str(i), service="search") for i in range(100)]
    client.bulk_action(create_items=search_accounts)

    return PodAPI(database_key=client.database_key, owner_key=client.owner_key)


def test_pod_version(api: PodAPI):
    assert "cargo" in api.pod_version


def test_create_schema(api: PodAPI):
    s = [
        {
            "type": "ItemPropertySchema",
            "itemType": "Person",
            "propertyName": "prop1",
            "valueType": "Text",
        },
        {
            "type": "ItemPropertySchema",
            "itemType": "Person",
            "propertyName": "prop2",
            "valueType": "Integer",
        },
    ]
    api.create_item(s[0])
    api.create_item(s[1])


def test_create_item(api: PodAPI):
    s = {
        "type": "Person",
        "prop1": "Alice",
    }
    api.create_item(s)


def test_get_item(api: PodAPI):
    s = {
        "type": "Person",
        "prop1": "Alice",
    }
    uid = api.create_item(s)

    result = api.get_item(uid)[0]
    assert result["type"] == "Person"
    assert result["prop1"] == "Alice"


def test_update_item(api: PodAPI):
    s = {
        "type": "Person",
        "prop1": "Alice",
    }
    uid = api.create_item(s)

    s = {
        "type": "Person",
        "id": uid,
        "prop1": "Bob",
        "prop2": 10,
    }
    api.update_item(s)
    result = api.get_item(uid)[0]
    assert result["type"] == "Person"
    assert result["prop1"] == "Bob"
    assert result["prop2"] == 10


def test_graphql_1(api: PodAPI):
   
    query = """
        query {
            Message {
                id
                subject
                sender {
                    id
                    displayName
                    service
                    owner {
                        id
                        displayName
                    }
                }
            }
        }
    """

    res = api.post("graphql", query).json()
    message = res["data"][0]
    # check selections
    assert message["subject"] == "Hello"
    assert message["sender"][0]["displayName"] == "Alice"
    assert message["sender"][0]["owner"][0]["displayName"] == "Alice"
    # check non-selections
    assert "dateCreated" not in message

@pytest.mark.skip(reason="TODO /graphQL should error on out-of-schema values")
def test_graphql_2(api: PodAPI):
    query = """
        query { 
            Message {
                id
                subject
                sender {
                    id
                    displayName
                    non_existent_value
                }
            }
        }
    """

    try:
        api.post("graphql", query)
        assert False
    except PodError as e:
        assert e.status == 400

@pytest.mark.skip(reason="TODO /graphQL should support query aggregate functions")
def test_graphql_3(api: PodAPI):
   
    query = """
        query { 
            count
            total
        }
    """

    try:
        api.post("graphql", query)
        assert False
    except PodError as e:
        assert e.status == 400


def test_graphql_4(api: PodAPI):

    query = """
        query {
            Person {
                id
                displayName
                ~owner (filter: {service: {eq: "whatsapp"}}) {
                    id
                    displayName
                    service
                    ~sender {
                        subject
                    }
                }
            }
        }
    """

    res = api.post("graphql", query).json()
    # check reverse edges
    for p in res["data"]:
        if p["~owner"][0]["service"] == "whatsapp":
            assert p["~owner"][0]["~sender"][0]["subject"] == "Hello"
            return
    assert False

@pytest.mark.skip(reason="TODO /graphQL should support query aggregate functions")
def test_graphql_5(api: PodAPI):

    query = """
        query {
            Account (filter: {dateCreated: {gte: 1654784703}}, limit: 10) {
                id
                displayName
            }
            count
            total
        }
    """

    res = api.post("graphql", query).json()
    # count and total
    try:
        assert res["count"] == 10 and res["total"] == 103
    except:
        assert False
