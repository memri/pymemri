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

    owner_edgelist = object.__getattribute__(account, "owner")
    owner_edgelist.append(owner_edge)
    owner_edgelist.extend([owner_edge])
    _ = owner_edgelist + [owner_edge]
    owner_edgelist += [owner_edge]
    owner_edgelist[0] = owner_edge
    owner_edgelist.insert(0, owner_edge)

    # Length 5: add_edge, append, extend, +=, insert
    assert len(account.owner) == 5


def test_edge_insert_wrong_target():
    account = Account()
    account_2 = Account()
    owner_edge = Edge(account, account_2, "owner")
    owner_edgelist = object.__getattribute__(account, "owner")

    # Insert one correct edge for __setitem__ and insert
    account.add_edge("owner", Person())

    with pytest.raises(TypeError):
        account.add_edge("owner", account_2)
    with pytest.raises(TypeError):
        owner_edgelist.append(owner_edge)
    with pytest.raises(TypeError):
        owner_edgelist.extend([owner_edge])
    with pytest.raises(TypeError):
        _ = owner_edgelist + [owner_edge]
    with pytest.raises(TypeError):
        owner_edgelist += [owner_edge]
    with pytest.raises(TypeError):
        owner_edgelist[0] = owner_edge
    with pytest.raises(TypeError):
        owner_edgelist.insert(0, owner_edge)

    # Length 1 from first add_edge
    assert len(account.owner)==1
