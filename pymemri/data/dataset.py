__all__ = ['filter_rows', 'Dataset']

from typing import List, Union
from pathlib import Path
from ..exporters.exporters import Query
from . import _central_schema

# Cell
# hide
def filter_rows(dataset: dict, filter_val=None) -> dict:
    missing_idx = set()
    for column in dataset.values():
        missing_idx.update([i for i, val in enumerate(column) if val == filter_val])
    return {
        k: [item for i, item in enumerate(v) if i not in missing_idx]
        for k, v in dataset.items()
    }

# Cell
class Dataset(_central_schema.Dataset):
    """
    The main Dataset class
    """
    requires_client_ref = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = None

    def _get_items(self):
        if self._client is None:
            raise ValueError("Dataset does not have associated PodClient.")
        if not len(self.entry):
            edges = self._client.get_edges(self.id)
            for e in self._client.get_edges(self.id):
                self.add_edge(e["name"], e["item"])

        return self.entry

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
        """
        Converts Dataset to a different format.

        Available formats:
        list: a 2-dimensional list, containing one dataset entry per row
        dict: a list of dicts, where each dict contains {column: value} for each column
        pd: a Pandas dataframe


        Args:
            dtype (str): Datatype of the returned dataset
            columns (List[str]): Column names of the dataset
            filter_missing (bool, optional): If true, all rows that contain `None` values are omitted.
                Defaults to True.

        Returns:
            Any: Dataset formatted according to `dtype`
        """
        return self._get_data(dtype, columns, filter_missing)

    def save(
        self, path: Union[Path, str], columns: List[str], filter_missing: bool = True
    ):
        """
        Save dataset to CSV.
        """
        result = self._get_data("pandas", columns, filter_missing)
        result.to_csv(path, index=False)
