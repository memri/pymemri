from typing import List, Optional

from pymemri.data.schema import Item, Person


class Dog(Item):
    name: Optional[str] = None
    age: Optional[int] = None
    bites: Optional[bool] = None
    weight: Optional[float] = None
    owner: List[Person] = []
