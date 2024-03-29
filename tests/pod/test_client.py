from time import sleep
from typing import List, Optional

import pytest

from pymemri.data.schema import Account, Edge, EmailMessage, Item, Person, PluginRun
from pymemri.data.schema.schema import SchemaMeta
from pymemri.examples.example_schema import Dog
from pymemri.pod.client import PodClient, PodError
from pymemri.pod.graphql_utils import GQLQuery


@pytest.fixture(scope="module")
def client():
    client = PodClient()
    return client


def setup_sync_items(client) -> List[Item]:
    existing = [EmailMessage(content=f"content_{i}") for i in range(3)]
    new_items = [EmailMessage(content=f"content_{i+3}") for i in range(3)]

    client.bulk_action(create_items=existing)

    all_items = existing + new_items
    for item in all_items:
        item.store(client)

    # Change existing property locally
    existing[0].content = "changed_0"

    # Add new property
    for i, item in enumerate(all_items):
        item.title = f"title_{i}"

    # Change existing property without local change
    client2 = PodClient(database_key=client.database_key, owner_key=client.owner_key)
    item = client2.get(existing[2].id)
    item.content = "remote_content"
    client2.update_item(item)

    # Change existing property with local change (conflict)
    item = client2.get(existing[0].id)
    item.content = "conflict"
    client2.update_item(item)

    return all_items


def test_connection(client: PodClient):
    assert client.api.test_connection()


def test_add_to_schema(client: PodClient):
    assert client.add_to_schema(
        SchemaMeta(name="testAddToSchema", url="example.com", version="0.1"),
        EmailMessage,
        Person,
        Account,
    )


def test_create(client: PodClient):
    assert client.create(EmailMessage(content="test content"))


def test_custom_item(client: PodClient):
    client.add_to_schema(SchemaMeta(name="testCustomItem", url="example.com", version="0.1"), Dog)
    dog = Dog(name="bob", age=3, weight=33.2)
    client.create(dog)

    dog_from_db = client.get(dog.id)
    assert dog_from_db.name == "bob"
    assert dog_from_db.age == 3
    assert dog_from_db.weight == 33.2


def test_create_edge(client: PodClient):
    account = Account(handle="Alice")
    email = EmailMessage(content="test content")

    assert client.bulk_action(create_items=[account, email])

    email.add_edge("sender", account)
    assert client.create_edge(email.get_edges("sender")[0])
    client.get_edges(email.id)
    assert len(client.get_edges(email.id))


def test_delete_edge(client: PodClient):
    # setup
    account = Account(handle="Alice")
    email = EmailMessage(content="test content")
    email.add_edge("sender", account)
    client.bulk_action(create_items=[account, email], create_edges=[email.get_edges("sender")[0]])

    senderEdges = email.get_edges("sender")
    assert len(senderEdges) == 1
    # delete the edge
    assert client.delete_edge(senderEdges[0])
    # check if deleted in Pod
    senderEdges = client.get_edges(email.id)
    assert len(senderEdges) == 0


def test_get_item(client: PodClient):
    person = Person(firstName="Alice")
    client.create(person)
    client.reset_local_db()
    person_from_db = client.get(person.id)
    assert person.firstName == person_from_db.firstName
    assert person.id == person_from_db.id


def test_update_item(client: PodClient):
    person_item = Person(firstName="Alice")
    client.create(person_item)
    person_item.lastName = "Awesome"
    client.update_item(person_item)
    client.reset_local_db()
    person_from_db = client.get(person_item.id, expanded=False)
    assert person_from_db.lastName == "Awesome"


def test_partial_update(client: PodClient):
    person_item = Person(firstName="Alice")
    client.create(person_item)
    person_from_db = client.get(person_item.id, expanded=False)

    # Test partial updating
    assert len(person_from_db._updated_properties) == 0

    # Change property
    person_from_db.displayName = "AliceAwesome"
    assert "displayName" in person_from_db._updated_properties
    client.update_item(person_from_db)
    assert len(person_from_db._updated_properties) == 0

    # Change non-property
    person_from_db._in_pod = None
    assert len(person_from_db._updated_properties) == 0

    # Empty update
    assert client.update_item(person_from_db)


def test_sync_local():
    client = PodClient()
    all_items = setup_sync_items(client)
    client.sync(priority="local")
    for i, item in enumerate(all_items):
        if i == 0:
            assert item.content == f"changed_{i}"
        elif i == 2:
            item.content == "remote_content"
        else:
            assert item.content == f"content_{i}"
        assert item.title == f"title_{i}"
        assert item._in_pod


def test_sync_remote():
    client = PodClient()
    all_items = setup_sync_items(client)
    client.sync(priority="remote")
    for i, item in enumerate(all_items):
        if i == 0:
            assert item.content == "conflict"
        elif i == 2:
            assert item.content == "remote_content"
        else:
            assert item.content == f"content_{i}"
        assert item.title == f"title_{i}"
        assert item._in_pod


def test_sync_newest():
    client = PodClient()
    all_items = setup_sync_items(client)
    client.sync(priority="newest")
    for i, item in enumerate(all_items):
        if i == 0:
            assert item.content == "conflict"
        elif i == 2:
            assert item.content == "remote_content"
        else:
            assert item.content == f"content_{i}"
        assert item.title == f"title_{i}"
        assert item._in_pod


def test_search(client: PodClient):
    person_item2 = Person.from_data(firstName="Bob")
    person_account = Account(service="testService")
    client.create(person_item2)
    client.create(person_account)
    person_item2.add_edge("account", person_account)
    client.create_edges(person_item2.get_edges("account"))
    client.reset_local_db()

    all_people = client.search({"type": "Person"}, include_edges=True)
    assert all([isinstance(p, Person) for p in all_people]) and len(all_people) > 0
    assert any([len(p.account) for p in all_people])
    assert all([item._in_pod for item in all_people])


def test_search_no_edges(client: PodClient):
    all_people = client.search({"type": "Person"}, include_edges=False)
    assert len(all_people)
    assert [len(person.get_all_edges()) == 0 for person in all_people]


def search_by_ids(client: PodClient):
    all_people = client.search({"type": "Person"}, include_edges=False)
    ids = [person.id for person in all_people]
    result = client.search({"ids": ids})
    assert [item.id for item in result] == ids


def test_paginate(client: PodClient):
    client.bulk_action(
        create_items=[Account(identifier=str(i), service="paginate_test") for i in range(100)]
    )

    client.reset_local_db()
    accounts = client.search({"type": "Account", "service": "paginate_test"})
    generator = client.search_paginate({"type": "Account", "service": "paginate_test"}, limit=10)
    accounts_paginated = []
    for page in generator:
        accounts_paginated.extend(page)

    assert len(accounts_paginated) == 100
    assert [a.id for a in accounts] == [a.id for a in accounts_paginated]
    assert all(a._in_pod for a in accounts_paginated)


def test_paginate_edge_cases(client: PodClient):
    result = client.search({"type": "Account", "service": "NonExistentService"})
    assert result == []

    paginator = client.search_paginate({"type": "Account", "service": "NonExistentService"})

    try:
        next(paginator)
    except Exception as e:
        assert isinstance(e, StopIteration)


def test_search_last_added(client: PodClient):
    person_item2 = Person.from_data(firstName="Last Person")
    client.create(person_item2)
    last_added = client.search_last_added(type="Person")
    assert last_added.firstName == "Last Person"


def test_search_gql(client: PodClient):
    client.bulk_action(create_items=[Person(firstName=str(i)) for i in range(100)])
    all_persons = client.search({"type": "Person"}, include_edges=False)
    person_ids = [p.id for p in all_persons]

    query = GQLQuery("query{Person{id}}")
    items = client.search_graphql(query)
    result_ids = [r.id for r in items]
    assert person_ids == result_ids


def test_bulk_create(client: PodClient):
    client.add_to_schema(SchemaMeta(name="testBulkCreate", url="example.com", version="0.1"), Dog)

    dogs = [Dog(name=f"dog number {i}") for i in range(100)]
    person = Person(firstName="Alice")
    edge1 = Edge(dogs[0], person, "owner")
    edge2 = Edge(dogs[1], person, "owner")

    assert client.bulk_action(create_items=dogs + [person], create_edges=[edge1, edge2])

    dogs = client.search({"type": "Dog"})
    dogs_with_edge = [item for item in dogs if len(item.get_all_edges())]

    print(len(dogs_with_edge))
    assert len(dogs_with_edge) == 2
    for d in dogs_with_edge:
        assert len(d.owner) > 0


def test_bulk_update_delete(client: PodClient):
    person1 = Person(firstName="Alice")
    person2 = Person(firstName="Bob")
    client.bulk_action(create_items=[person1, person2])

    person1.firstName = "updated"
    to_delete = [person2]
    to_update = [person1]

    client.bulk_action(delete_items=to_delete, update_items=to_update)

    client.reset_local_db()

    with pytest.raises(ValueError):
        client.get(person2.id)

    assert client.get(person1.id).firstName == "updated"


def test_plugin_status(client: PodClient):
    run = PluginRun(containerImage="", pluginName="", pluginModule="")
    client.create(run)
    assert client.plugin_status([run.id])[run.id] == {"status": "unreachable"}


def test_create_account():
    # Create client with new account
    client = PodClient()
    owner_key = client.owner_key
    database_key = client.database_key

    # Create another client with same keys
    client = PodClient(owner_key=owner_key, database_key=database_key, create_account=False)
    client.search({"type": "PodUserAccount"})

    # Create new client + account with same keys only raises warning
    client = PodClient(owner_key=owner_key, database_key=database_key, create_account=True)
    client.search({"type": "PodUserAccount"})

    # New pod without create_account throws error, upon usage
    client = PodClient(create_account=False, owner_key=PodClient.generate_random_key())
    with pytest.raises(PodError):
        client.add_to_schema(SchemaMeta(name="test", url="example.com", version="0.1"), Person)


def test_update_schema():
    client = PodClient()

    client2 = PodClient(
        owner_key=client.owner_key,
        database_key=client.database_key,
    )

    class TestItem(Item):
        field1: str

    client.add_to_schema(
        SchemaMeta(name="testUpdateSchema", url="example.com", version="0.1"), TestItem
    )

    client.bulk_action(
        create_items=[
            TestItem(field1="test1"),
        ]
    )

    items = client.search_typed(TestItem)
    assert len(items) == 1

    class TestItem(Item):
        field1: str
        field2: Optional[str]

    client2.add_to_schema(
        SchemaMeta(name="testUpdateSchema", url="example.com", version="0.2"), TestItem
    )
    # Create data for search
    client2.bulk_action(
        create_items=[
            TestItem(field1="test2.1", field2="test2.2"),
        ]
    )

    items = client2.search_typed(TestItem, include_edges=False)

    assert len(items) == 2
    assert items[1].field2 == "test2.2"
