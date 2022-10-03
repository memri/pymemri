import json
import zipfile
from pathlib import Path

Path.ls = lambda x: list(x.iterdir())
PYI_HOME = Path.cwd().parent
PYI_TESTDATA = PYI_HOME / "test" / "data"
HOME_DIR = Path.home()
MODEL_DIR = HOME_DIR / ".memri" / "models"
MEMRI_S3 = "https://memri.s3-eu-west-1.amazonaws.com"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path):
    with open(path) as json_file:
        return json.load(json_file)


def write_json(obj, fname, indent=4):
    with open(fname, "w") as file_out:
        json.dump(obj, file_out, indent=indent)


def unzip(f, dest):
    with zipfile.ZipFile(str(f)) as zf:
        zf.extractall(str(dest))
