from pathlib import Path

from loguru import logger

from ..data.basic import read_json

PYMEMRI_FOLDER = ".pymemri"
POD_KEYS_FOLDER = "pod_keys"
POD_KEYS_FILENAME = "keys.json"
POD_KEYS_FULL_FOLDER = Path.home() / ".pymemri" / POD_KEYS_FOLDER
DEFAULT_POD_KEY_PATH = POD_KEYS_FULL_FOLDER / POD_KEYS_FILENAME


def read_pod_key(key_type, file=DEFAULT_POD_KEY_PATH):
    try:
        json = read_json(file)
    except:
        raise ValueError(
            f"Trying to read key from {file}, but file or key does not exist"
        ) from None
    try:
        key = json[key_type]
        logger.info(f"reading {key_type} from {file}")
        return key
    except:
        raise ValueError(f"{key_type} not specified in {file}") from None
