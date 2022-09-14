from typing import List

import pytest

from pymemri.data.oauth import OauthFlow
from pymemri.data.schema import Account, Edge, EdgeList, EmailMessage, Item, Person
from pymemri.pod.client import PodClient
from pymemri.pod.graphql_utils import GQLQuery


class Dog(Item):
    properties = Item.properties + ["name", "age", "bites", "weight"]
    edges = Item.edges + ["owner"]

    def __init__(
        self,
        name: str = None,
        age: int = None,
        bites: bool = False,
        weight: float = None,
        owner: EdgeList["Person"] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.name = name
        self.age = age
        self.bites = bites
        self.weight = weight

        self.owner = EdgeList("owner", "Person", owner)


@pytest.fixture(scope="module")
def client():
    return PodClient()


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
    assert client.add_to_schema(EmailMessage, Person, Account)


def test_create(client: PodClient):
    assert client.create(EmailMessage(content="test content"))


def test_custom_item(client: PodClient):
    client.add_to_schema(Dog)
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
    person_from_db.non_property = "test"
    assert len(person_from_db._updated_properties) == 0

    # Empty update
    assert client.update_item(person_from_db)


def test_sync_local():
    client = PodClient()
    client.add_to_schema(EmailMessage)
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
    client.add_to_schema(EmailMessage)
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
    client.add_to_schema(EmailMessage)
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


def test_sync_error():
    client = PodClient()
    client.add_to_schema(EmailMessage)
    all_items = setup_sync_items(client)
    try:
        client.sync(priority="error")
        assert False
    except Exception as e:
        assert isinstance(e, ValueError)


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
    assert client.get(person2.id, include_deleted=True).deleted
    assert client.get(person1.id).firstName == "updated"


def test_oauth_search(client: PodClient):
    oauth_item = OauthFlow(accessToken="", refreshToken="")
    client.add_to_schema(oauth_item)
    client.create(oauth_item)
    assert client.get_oauth_item() != None
