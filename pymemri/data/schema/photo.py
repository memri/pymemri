import io
import json
from hashlib import sha256
from pathlib import Path
from typing import Any, List, Optional, Tuple

import numpy as np
from PIL import ExifTags, Image

from ._central_schema import File, Photo

DEFAULT_ENCODING = "PNG"


class Photo(Photo):
    data: Optional[bytes] = None

    def show(self):
        raise NotImplementedError()

    @property
    def size(self):
        return self.width, self.height

    @classmethod
    def from_path(cls, path: Path, size: Optional[Tuple[int]] = None):
        pil_image = Image.open(path)
        if size is not None:
            pil_image = pil_image.resize(size)
        return cls.from_PIL(pil_image)

    @classmethod
    def from_np(cls, data: np.array, size: Optional[Tuple[int]] = None):
        pil_image = Image.fromarray(data)
        if size is not None:
            pil_image = pil_image.resize(size)
        return cls.from_PIL(pil_image)

    @classmethod
    def from_bytes(cls, _bytes, size: Optional[Tuple[int]] = None):
        image_stream = io.BytesIO(_bytes)
        pil_image = Image.open(image_stream)
        if size is not None:
            pil_image = pil_image.resize(size)
        return cls.from_PIL(pil_image, _bytes)

    @classmethod
    def from_PIL(cls, image: Image.Image, bytes_: Optional[bytes] = None):
        encoding, mode, shape = cls.infer_PIL_metadata(image)
        w, h, c = shape
        exif_data = cls.extract_exif(image)
        _bytes = bytes_ or cls.PIL_to_bytes(image, encoding)

        res = cls(
            data=_bytes,
            height=h,
            width=w,
            channels=c,
            encoding=encoding,
            mode=mode,
            exifData=exif_data,
            id=cls.create_id(),
        )
        file = File(sha256=sha256(_bytes).hexdigest())
        res.add_edge("file", file)
        file.id = file.create_id()
        return res

    @staticmethod
    def PIL_to_bytes(pil_image, encoding):
        byte_io = io.BytesIO()
        pil_image.save(byte_io, encoding)
        return byte_io.getvalue()

    @staticmethod
    def extract_exif(pil_image: Image.Image) -> Optional[str]:
        # extract exif
        exif_dict = {}
        exif_data = pil_image.getexif()
        for k, v in exif_data.items():
            if k in ExifTags.TAGS:
                exif_dict[ExifTags.TAGS[k]] = str(v)  # may include bytes
        if len(exif_dict.keys()) == 0:
            exif_dict = None
        return json.dumps(exif_dict)

    @staticmethod
    def infer_PIL_metadata(pil_image: Image.Image):
        encoding = pil_image.format or DEFAULT_ENCODING
        mode = pil_image.mode
        size = pil_image.size
        if len(size) == 3:
            w, h, c = size
        elif len(size) == 2:
            w, h = size
            c = 1
        else:
            raise ValueError()
        return encoding, mode, (w, h, c)

    def to_PIL(self) -> Image.Image:
        if self.data is None:
            raise ValueError("Photo object has no data")

        return Image.open(io.BytesIO(self.data))

    def to_np(self) -> np.array:
        pil_img = self.to_PIL()
        return np.asarray(pil_img)
