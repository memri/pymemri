from pathlib import Path
from typing import Any, ClassVar, List, Optional, Union

from pydantic import PrivateAttr

from ...exporters.exporters import Query
from ._central_schema import Dataset


def filter_rows(dataset: dict, filter_val=None) -> dict:
    missing_idx = set()
    for column in dataset.values():
        missing_idx.update([i for i, val in enumerate(column) if val == filter_val])
    return {
        k: [item for i, item in enumerate(v) if i not in missing_idx] for k, v in dataset.items()
    }


class Dataset(Dataset):
    requires_client_ref: ClassVar[bool] = True
    _client: Optional[Any] = PrivateAttr(None)

    def _get_items(self):
        if self._client is None:
            raise ValueError("Dataset does not have associated PodClient.")
        if not len(self.entry):
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

    def _infer_columns(self):
        column_names = []
        for feature in self.feature:
            column_name = "data." + feature.propertyName
            column_names.append(column_name)

        # TODO infer columns for different label types
        column_names.append("annotation.labelValue")

        return column_names

    def to(self, dtype: str, columns: Optional[List[str]] = None, filter_missing: bool = True):
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
        if columns is None:
            columns = self._infer_columns()
        return self._get_data(dtype, columns, filter_missing)

    def save(self, path: Union[Path, str], columns: List[str], filter_missing: bool = True):
        """
        Save dataset to CSV.
        """
        result = self._get_data("pandas", columns, filter_missing)
        result.to_csv(path, index=False)
