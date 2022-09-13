from pathlib import Path
from typing import Any, List, Union

from . import _central_schema
from .itembase import EdgeList, Item


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
