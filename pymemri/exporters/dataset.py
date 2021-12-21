from typing import Dict, List

from ..pod.client import PodClient
from ..data.itembase import Item


class DataColumn:
    def __init__(self, definition, name=None):
        self.definition = definition
        self.edges, self.property = self._parse(definition)
        self.name = name if name is not None else definition

    @staticmethod
    def _parse(definition):
        definition = definition.split(".")
        edges = definition[:-1]
        prop = definition[-1]
        return edges, prop


def get_column_value(client: PodClient, item: Item, column: DataColumn):
    for edge in column.edges:
        if edge not in item.edges or not isinstance(getattr(item, edge), list):
            return None

        if len(getattr(item, edge)) == 0:
            item = client.get(item.id)
        
        if len(getattr(item, edge)) == 0:
            return None

        item = getattr(item, edge)[0]

    return getattr(item, column.property, None)


def get_column_values(client, item, columns):
    values = [get_column_value(item, column) for column in columns]


def export_dataset(client: PodClient, items: List[str], columns: List[str], filter_incomplete=True) -> Dict[str, list]:
    columns = [DataColumn(col) for col in columns]
    dataset = {column.name: list() for column in columns}
    for item in items:
        values = get_column_values(client, item, columns)
        if filter_incomplete and None in values:
            continue
        for col, value in zip(columns, values):
            dataset[col.name].append(value)
