from datetime import datetime
from typing import List, Optional, Union

from pydantic import PrivateAttr

from pymemri.data.schema import Item, Message, Person, Tweet


class Dog(Item):
    _hasBeenFed: bool = PrivateAttr(False)

    # Properties
    name: Optional[str] = None
    age: Optional[int] = None
    bites: Optional[bool] = None
    weight: Optional[float] = None
    dateOfBirth: Optional[datetime] = None

    # Edges
    owner: List[Person] = []
    referencedBy: List[Union[Message, Tweet]] = []
