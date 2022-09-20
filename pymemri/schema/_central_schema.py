from typing import Optional

from .item import Item


class Account(Item):
    handle: Optional[str] = None
