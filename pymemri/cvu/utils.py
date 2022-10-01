from pathlib import Path
from typing import List

import pymemri

from ..data.schema import CVUStoredDefinition

CVU_BASE_PATH = Path(pymemri.__file__).parent / "cvu" / "definitions"


def get_default_cvu(name: str, base_path: Path = CVU_BASE_PATH) -> CVUStoredDefinition:
    """
    Get a CVU by name.
    """
    path = Path(base_path) / name
    cvu_str = Path(path).read_text()
    return CVUStoredDefinition(definition=cvu_str, name=name, externalId=name)


def list_default_cvus(base_path: Path = CVU_BASE_PATH) -> List[str]:
    """
    List all CVUs available in pymemri.
    """
    path = Path(base_path)
    cvus = path.glob("*.cvu")
    cvu_names = [path.name for path in cvus]
    return cvu_names
