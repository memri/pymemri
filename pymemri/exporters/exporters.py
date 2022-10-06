from typing import TYPE_CHECKING, Any, List

import pandas as pd

if TYPE_CHECKING:
    from ..data.schema import Item
    from ..pod.client import PodClient


class Query:
    def __init__(self, *properties: List[str]):
        """
        A Query implements functionality to retrieve data from the pod to a tabular format.

        Given a list of `properties`, the `execute` method queries the pod for a set of given items,
        and retrieves the properties for each item if it exists. Note that a properties can be nested behind
        multiple edges, such as "sender.owner.firstName".
        """
        self.properties = list(properties)

    def traverse_edges(
        self, client: "PodClient", items: List["Item"], edges: List[str]
    ) -> List["Item"]:
        items = items.copy()

        for edge in edges:
            ids_to_query = list()
            query_item_idx = list()
            for i in range(len(items)):
                item = items[i]
                if item is None:
                    continue
                # Replace item with target item. If the edge is empty, it has to be queried again.
                try:
                    if edge not in item.edges:
                        items[i] = None
                    else:
                        items[i] = getattr(item, edge)[0]
                except Exception:
                    ids_to_query.append(item.id)
                    query_item_idx.append(i)
                    items[i] = None

            new_items = client.search({"ids": ids_to_query})
            for i, new_item in zip(query_item_idx, new_items):
                try:
                    items[i] = getattr(new_item, edge)[0]
                except Exception:
                    items[i] = None
        return items

    def get_property_values(self, client: "PodClient", prop: str, items: List["Item"]) -> list:
        edges, prop_name = self.parse_property(prop)
        target_items = self.traverse_edges(client, items, edges)

        result = [getattr(item, prop_name, None) for item in target_items]
        return result

    @staticmethod
    def parse_property(prop: str):
        prop = prop.split(".")
        edges = prop[:-1]
        prop = prop[-1]
        return edges, prop

    def convert_dtype(self, result, dtype):
        if dtype == "dict":
            return result
        elif dtype == "list":
            return [result[prop] for prop in self.properties]
        elif dtype in {"pandas", "pd", "df"}:
            return pd.DataFrame.from_dict(result)
        else:
            raise ValueError(f"Unknown dtype: {dtype}")

    def execute(self, client: "PodClient", items: List["Item"], dtype="dict") -> Any:
        result = {prop: self.get_property_values(client, prop, items) for prop in self.properties}
        return self.convert_dtype(result, dtype)
