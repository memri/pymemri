import numpy as np
import pytest
from PIL import Image

from pymemri.data.schema import Photo
from pymemri.data.schema.photo import DEFAULT_ENCODING
from pymemri.data.schema.schema import SchemaMeta
from pymemri.pod.client import PodClient
from pymemri.test_utils import get_project_root


@pytest.fixture
def photo_path():
    return get_project_root() / "nbs" / "images" / "labrador.jpg"


def test_photo_from_path(photo_path):
    photo = Photo.from_path(photo_path)
    assert photo.encoding == "JPEG"
    assert photo.mode == "RGB"
    assert photo.width and photo.height


def test_photo_from_bytes(photo_path):
    with open(photo_path, "rb") as f:
        b = f.read()

    photo_bytes = Photo.from_bytes(b)
    assert photo_bytes.encoding == "JPEG"
    assert photo_bytes.mode == "RGB"
    assert photo_bytes.width and photo_bytes.height


def test_photo_from_numpy(photo_path):
    np_image = np.asarray(Image.open(photo_path))
    photo_np = Photo.from_np(np_image)

    assert photo_np.encoding == DEFAULT_ENCODING
    assert photo_np.mode == "RGB"
    assert photo_np.width and photo_np.height


def test_create_get_photo(photo_path):
    photo = Photo.from_path(photo_path)

    client = PodClient()
    client.add_to_schema(SchemaMeta(name="test_dataset", url="example.com", version="0.1"), Photo)
    client.create_photo(photo, asyncFlag=False)

    client.reset_local_db()
    photo_2 = client.get_photo(photo.id)
    assert isinstance(photo_2.to_PIL(), Image.Image)

    p2_json = photo_2.to_json()
    for k, v in photo.to_json().items():
        assert p2_json[k] == v
