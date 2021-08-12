# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/cvu.utils.ipynb (unless otherwise specified).

__all__ = ['get_cvu', 'BASE_PATH']

# Cell
from ..data.basic import read_file
from ..data.schema import CVUStoredDefinition
from pathlib import Path
import pymemri

# Cell
BASE_PATH = Path(pymemri.__file__).parent.parent / "cvu"

def get_cvu(name, base_path=BASE_PATH):
    path = Path(base_path) / name
    cvu_str = read_file(path)
    return CVUStoredDefinition(definition=cvu_str, name=name, externalId=name)