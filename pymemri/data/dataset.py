# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/data.dataset.ipynb (unless otherwise specified).

__all__ = ['filter_rows', 'Dataset']

# Cell
# hide
from typing import List, Union
from pathlib import Path
from .itembase import Item
from ..exporters.exporters import Query

# Cell
def filter_rows(dataset: dict, filter_val=None) -> dict:
    missing_idx = set()
    for column in dataset.values():
        missing_idx.update([i for i, val in enumerate(column) if val == filter_val])
    return {
        k: [item for i, item in enumerate(v) if i not in missing_idx] for k, v in dataset.items()
    }

# Cell
class Dataset(Item):
    """
    Temporary dataset schema, needs update when MVP2 is done.
    """
    properties= Item.properties + ["name", "queryStr"]
    edges = Item.edges + ["item"]

    def __init__(self, name: str = None, queryStr: str = None, item: list = None, **kwargs):
        super().__init__(**kwargs)
        self.queryStr = queryStr
        self.name = name
        self.item: list = item if item is not None else []

    def _get_items(self):
        if self._client is None:
            raise ValueError("Dataset does not have associated PodClient.")
        if not len(self.item):
            edges = self._client.get_edges(self.id)
            for e in self._client.get_edges(self.id):
                self.add_edge(e["name"], e["item"])

        return self.item

    def _get_data(self, dtype: str, columns: List[str], filter_missing: bool = True):
        if self._client is None:
            raise ValueError("Dataset does not have associated PodClient.")
        items = self._get_items()

        query = Query("id", *columns)
        result = query.execute(self._client, items)
        if filter_missing:
            result = filter_rows(result, filter_val=None)
        return query.convert_dtype(result, dtype)

    def to(self, dtype: str, columns: List[str], filter_missing: bool = True):
        return self._get_data(dtype, columns, filter_missing)

    def save(self, path: Union[Path, str], columns: List[str], filter_missing: bool = True):
        result = self._get_data("pandas", columns, filter_missing)
        result.to_csv(path, index=False)