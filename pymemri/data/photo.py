__all__ = ['DEFAULT_ENCODING', 'show_images', 'Photo']

from .itembase import Item, EdgeList
from ._central_schema import File
from .basic import *
from matplotlib.pyplot import imshow
from matplotlib import patches
from matplotlib.collections import PatchCollection
from numpy.linalg import norm
from hashlib import sha256
import matplotlib.pyplot as plt
import math
import numpy as np
import io
from PIL import Image
from hashlib import sha256
from typing import Any

# Cell
DEFAULT_ENCODING = "PNG"

# Cell
def show_images(images, cols = 3, titles = None):
    image_list = [x.data for x in images] if isinstance(images[0], Photo) else images
    assert((titles is None) or (len(image_list) == len(titles)))
    n_images = len(image_list)
    if titles is None: titles = ["" for i in range(1,n_images + 1)]
    fig = plt.figure()
    for n, (image, title) in enumerate(zip(image_list, titles)):
        a = fig.add_subplot(int(np.ceil(n_images/float(cols))), cols , n + 1)
        a.axis('off')
        if image.ndim == 2:
            plt.gray()
        plt.imshow(image[:,:,::-1])
        a.set_title(title)
    fig.set_size_inches(np.array(fig.get_size_inches()) * n_images)
    plt.show()


class Photo(Item):

    properties = Item.properties + ["width", "height", "channels", "encoding", "mode"]
    edges = Item.edges + ["file"]

    def __init__(
        self,
        data: Any = None,
        includes: Any = None,  # TODO
        thumbnail: Any = None,  # TODO
        height: int = None,
        width: int = None,
        channels: int = None,
        encoding: str = None,
        mode: str = None,
        file: EdgeList[File] = None,
        _file_created: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.private = ["data", "embedding", "path"]  # TODO
        self.height = height
        self.width = width
        self.channels = channels
        self.encoding = encoding
        self.mode = mode
        self.file = file if file is not None else []
        self.data = data
        self._file_created = _file_created

    def show(self):
        fig, ax = plt.subplots(1)
        fig.set_figheight(15)
        fig.set_figwidth(15)
        ax.axis("off")
        imshow(self.data[:, :, ::-1])
        fig.set_size_inches((6, 6))
        plt.show()

    @property
    def size(self):
        return self.width, self.height

    @classmethod
    def from_data(cls, *args, **kwargs):
        res = super().from_data(*args, **kwargs)
        if res.file:
            res.file[0]  # TODO
        return res

    @classmethod
    def from_path(cls, path, size=None):
        pil_image = Image.open(path)
        encoding, mode, shape = cls.infer_PIL_metadata(pil_image)
        w, h, c = shape
        _bytes = cls.PIL_to_bytes(pil_image, encoding)

        res = cls(
            data=_bytes, height=h, width=w, channels=c, encoding=encoding, mode=mode
        )
        file = File.from_data(sha256=sha256(_bytes).hexdigest())
        res.add_edge("file", file)
        return res

    @classmethod
    def from_np(cls, data, size=None, *args, **kwargs):
        pil_image = Image.fromarray(data)
        if size is not None:
            pil_image = pil_image.resize(size)
        encoding, mode, shape = cls.infer_PIL_metadata(pil_image)
        w, h, c = shape
        _bytes = cls.PIL_to_bytes(pil_image, encoding)

        res = cls(
            data=_bytes, height=h, width=w, channels=c, encoding=encoding, mode=mode
        )
        file = File.from_data(sha256=sha256(_bytes).hexdigest())
        res.add_edge("file", file)
        return res

    @classmethod
    def from_bytes(cls, _bytes):
        image_stream = io.BytesIO(_bytes)
        pil_image = Image.open(image_stream)
        encoding, mode, shape = cls.infer_PIL_metadata(pil_image)
        w, h, c = shape

        res = cls(
            data=_bytes, height=h, width=w, channels=c, encoding=encoding, mode=mode
        )
        file = File.from_data(sha256=sha256(_bytes).hexdigest())
        res.add_edge("file", file)
        return res

    @staticmethod
    def PIL_to_bytes(pil_image, encoding):
        byte_io = io.BytesIO()
        pil_image.save(byte_io, encoding)
        return byte_io.getvalue()

    @staticmethod
    def infer_PIL_metadata(pil_image):
        encoding = pil_image.format or DEFAULT_ENCODING
        mode = pil_image.mode
        size = pil_image.size
        if len(size) == 3:
            w, h, c = size
        if len(size) == 2:
            w, h = size
            c = 1
        else:
            raise Error
        return encoding, mode, (w, h, c)

    def to_PIL(self):
        if self.data is None:
            raise ValueError("Photo object has no data")

        return Image.open(io.BytesIO(self.data))

    def to_np(self):
        pil_img = self.to_PIL()
        return np.asarray(pil_img)
