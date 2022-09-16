from pymemri.data.itembase import EdgeList, Item
from pymemri.data.schema import Person


class Dog(Item):
    properties = Item.properties + ["name", "age", "bites", "weight"]
    edges = Item.edges + ["friend"]

    def __init__(
        self,
        name: str = None,
        age: int = None,
        bites: bool = False,
        weight: float = None,
        friend: EdgeList[Person] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name
        self.age = age
        self.bites = bites
        self.weight = weight
        self.friend = EdgeList("friend", Person, friend)
