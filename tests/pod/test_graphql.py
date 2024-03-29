import random
import uuid

import pytest

from pymemri.data.schema import Account, Edge, Message, Person
from pymemri.pod.api import PodAPI, PodError
from pymemri.pod.client import PodClient
from pymemri.pod.graphql_utils import GQLQuery


@pytest.fixture(scope="module")
def api():
    """
    TODO copied from test_api, clean this up for graphQL
    """
    client = PodClient()

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


def test_format_query():
    query = GQLQuery(
        """query {
        Account(filter: {eq: {service: "$service"}})
    }
    """
    )

    q = query.format({"service": "test"})
    assert (
        query
        == """query {
        Account(filter: {eq: {service: "test"}})
    }
    """
    )


def test_graphql_1(api: PodAPI):

    query = """
        query {
            Message {
                subject
                sender {
                    displayName
                    service
                    owner {
                        displayName
                    }
                }
            }
        }
    """

    client = PodClient()
    client.api = api
    items = client.search_graphql(query)
    message = items[0]
    # check item type
    assert type(message).__name__ == "Message"
    # check selections
    assert message.subject == "Hello"
    assert message.sender[0].displayName == "Alice"
    assert message.sender[0].owner[0].displayName == "Alice"
    # base properties should exist
    assert getattr(message, "dateCreated", None)
    # non-selections should be absent
    assert getattr(message, "service", None) == None


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

    query = GQLQuery(
        """
        query {
            Person {
                id
                displayName
                ~owner (filter: {service: {eq: "$service"}}) {
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
    )
    query.format(service="whatsapp")

    res = api.graphql(query)
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
