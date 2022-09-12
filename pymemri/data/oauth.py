

from typing import List, Union, Any
from pathlib import Path
from .itembase import Item, EdgeList
from . import _central_schema

class OauthFlow(Item):
    description = """TBD"""
    properties = Item.properties + ["accessToken", "refreshToken", "accessTokenSecret"]
    edges = Item.edges + []

    def __init__(
        self,
        accessToken: str = None,
        refreshToken: str = None,
        accessTokenSecret: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.accessToken: Optional[str] = accessToken
        self.refreshToken: Optional[str] = refreshToken
        self.accessTokenSecret: Optional[str] = accessTokenSecret