from time import sleep
from typing import List
from pymemri.pod.client import PodClient
from pymemri.data.schema import Item
import pytest
from pymemri.data.schema import Photo, File
import numpy as np


@pytest.fixture(scope="module")
def client():
    return PodClient()

@pytest.fixture
def photo():
    x = np.random.randint(0, 255+1, size=(640, 640), dtype=np.uint8)
    return Photo.from_np(x)

def test_create_file(client: PodClient, photo: Photo):
    client.add_to_schema(File, Photo)
    file = photo.file[0]
    assert client.create(file)
    assert client.upload_file(photo.data)
    sleep(1)

    data = client.get_file(file.sha256)
    assert photo.data == data

def test_create_photo(client: PodClient, photo: Photo):
    client.add_to_schema(Photo)
    client.create_photo(photo)
    sleep(1)

    client.reset_local_db()
    photo_from_db = client.get_photo(photo.id)
    assert photo_from_db.data == photo.data
