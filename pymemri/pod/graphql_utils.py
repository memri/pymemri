from collections import UserString
from operator import contains
import string
from typing import Dict, Optional, Any


class GQLQuery(UserString):
    delimiter = "$"

    def __init__(self, query_string: str, variables: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(query_string)
        if variables:
            self.format(variables)

    def format(self, variables: Optional[Dict[str, Any]] = None, **kwargs) -> "GQLQuery":
        self.data = string.Template(self.data).substitute(variables, **kwargs)
        return self

def gql(query_string: str, variables: Optional[Dict[str, Any]] = None) -> GQLQuery:
    """
    Separate constructor for `GQLQuery` with interface similar to https://github.com/graphql-python/gql
    """
    return GQLQuery(query_string, variables)
