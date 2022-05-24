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
        Account(identifier="Alice", service="whatsapp"),
        Account(identifier="Alice", service="instagram"),
        Account(identifier="Alice", service="gmail"),
    ]

    message = Message(service="whatsapp", subject="Hello")
    edges = [Edge(account, person, "owner") for account in accounts]
    edges += [Edge(message, accounts[0], "sender")]
    client.bulk_action(create_items=accounts + [person, message], create_edges=edges)

    # Create data for search
    search_accounts = [Account(identifier=str(i), service="search") for i in range(100)]
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
   
    # query = """
    #     query {
    #         Person {
    #             id
    #             displayName
    #             ~owner  ??
    #         }
    #     }
    # """
    query = """
        query {
            Message {
                id
                subject
                service
                sender {
                    id
                    displayName
                    identifier
                    owner {
                        id
                        displayName
                    }
                }
            }
        }
    """

    res = api.post("graphql", query).json()
    # check selections
    assert res[0]["subject"] == "Hello"
    assert res[0]["sender"][0]["identifier"] == "Alice"
    assert res[0]["sender"][0]["owner"][0]["displayName"] == "Alice"
    # check non-selections
    assert "dateCreated" not in res[0]["sender"][0]


def test_graphql_2(api: PodAPI):
   
    query = """
        query { 
            Message {
                id
                subject
                sender {
                    id
                    identifier
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
        assert e.message == "Failure: Property non_existent_value does not exist in schema"


    
