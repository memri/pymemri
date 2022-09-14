import string
from collections import UserString
from typing import Any, Dict, Optional


class GQLQuery(UserString):
    def __init__(self, query_string: str, variables: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(query_string)
        if variables:
            self.format(variables)

    def format(self, variables: Optional[Dict[str, Any]] = None, **kwargs) -> "GQLQuery":
        self.data = string.Template(self.data).substitute(variables, **kwargs)
        return self
