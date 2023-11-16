from time import sleep
from typing import List

import numpy as np
import pytest

from pymemri.data.schema import File, Item, Photo
from pymemri.pod.client import PodClient


@pytest.fixture(scope="module")
def client():
    return PodClient()


@pytest.fixture
def photo():
    x = np.random.randint(0, 255 + 1, size=(640, 640), dtype=np.uint8)
    return Photo.from_np(x)


def test_create_file(client: PodClient, photo: Photo):
    file = photo.file[0]
    assert client.create(file)
    assert client.upload_file(photo.data)
    sleep(1)

    data = client.get_file(file.sha256)
    assert photo.data == data


def test_create_photo(client: PodClient, photo: Photo):
    client.create_photo(photo)
    sleep(1)

    client.reset_local_db()
    photo_from_db = client.get_photo(photo.id)
    assert photo_from_db.data == photo.data


def test_delete_file(client: PodClient):
    # setup
    files = client.search_typed(File)
    sha256 = files[-1].sha256

    # check file data exists
    file_data = client.get_file(sha256)
    assert file_data

    client.get(files[-1].id)

    client.delete_file(files[-1].id)

    client.reset_local_db()
    try:
        client.get(files[-1].id)
        assert False  # should not be able to get the file item
    except Exception as e:
        pass

    try:
        client.get_file(sha256)
        assert False  # should not be able to get the file
    except Exception as e:
        pass
