import pytest
from pymemri.pod.client import PodClient
from pymemri.data.schema import Account, Person
from pymemri.data.itembase import Edge

@pytest.fixture
def client():
    client = PodClient()
    client.add_to_schema(Account, Person)
    return client


def test_edge_insert_correct_target():
    account = Account()
    person = Person()
    owner_edge = Edge(account, person, "owner")

    account.add_edge("owner", person)
    account.owner.append(owner_edge)
    account.owner.extend([owner_edge])
    _ = account.owner + [owner_edge]
    account.owner += [owner_edge]
    account.owner.__radd__([owner_edge])
    account.owner[0] = owner_edge
    account.owner.insert(0, owner_edge)


def test_edge_insert_wrong_target():
    account = Account()
    account_2 = Account()
    owner_edge = Edge(account, account_2, "owner")

    # Insert one correct edge for __setitem__ and insert
    account.add_edge("owner", Person())

    with pytest.raises(TypeError):
        account.add_edge("owner", account_2)
    with pytest.raises(TypeError):
        account.owner.append(owner_edge)
    with pytest.raises(TypeError):
        account.owner.extend([owner_edge])
    with pytest.raises(TypeError):
        _ = account.owner + [owner_edge]
    with pytest.raises(TypeError):
        account.owner += [owner_edge]
    with pytest.raises(TypeError):
        account.owner.__radd__([owner_edge])
    with pytest.raises(TypeError):
        account.owner[0] = owner_edge
    with pytest.raises(TypeError):
        account.owner.insert(0, owner_edge)