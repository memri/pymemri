# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/data.photo.ipynb (unless otherwise specified).

__all__ = ['show_images', 'get_size', 'resize', 'get_height_width_channels', 'Photo']

# Cell
from .schema import Item

# Cell
from .schema import *
from .basic import *
from matplotlib.pyplot import imshow
from matplotlib import patches
from matplotlib.collections import PatchCollection
from numpy.linalg import norm
from hashlib import sha256
import cv2
import matplotlib.pyplot as plt
import math
import numpy as np
import io
from PIL import Image
from hashlib import sha256
from typing import Any

# Cell
NUMPY, BYTES = "numpy", "bytes"

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

def get_size(img, maxsize):
    s = img.shape
    assert len(s) > 1
    div = max(s) / maxsize
    return (int(s[1]//div), int(s[0]//div))

def resize(img, maxsize):
    size = get_size(img, maxsize)
    return cv2.resize(img, dsize=size, interpolation=cv2.INTER_CUBIC)

def get_height_width_channels(img):
    s = img.shape
    if len(s) == 2: return s[0], s[1], 1
    else: return img.shape

# Cell
class Photo(Item):

    properties = Item.properties + ["width", "height", "channels", "encoding"]
    edges = Item.edges + ["file"]

    def __init__(
        self,
        data: Any=None,
        includes: Any=None,
        thumbnail: Any=None,
        height: int=None,
        width: int=None,
        channels: int=None,
        encoding: str=None,
        file: list=None,
        _file_created: bool=False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.private = ["data", "embedding", "path"]
        self.height = height
        self.width = width
        self.channels = channels
        self.encoding = encoding
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

    @classmethod
    def from_data(cls, *args, **kwargs):
        res = super().from_data(*args, **kwargs)
        if res.file:
            res.file[0]
        return res

    @classmethod
    def from_path(cls, path, size=None):
        data = cv2.imread(str(path))
        res = cls.from_np(data, size)
        return res

    @classmethod
    def from_np(cls, data, size=None, *args, **kwargs):
        if size is not None:
            data = resize(data, size)
        h, w, c = get_height_width_channels(data)
        res = cls(
            data=data, height=h, width=w, channels=c, encoding=NUMPY, *args, **kwargs
        )
        file = File.from_data(sha256=sha256(data.tobytes()).hexdigest())
        res.add_edge("file", file)
        return res

    @classmethod
    def from_bytes(cls, _bytes):
        image_stream = io.BytesIO(_bytes)
        pil_image = Image.open(image_stream)
        size = pil_image.size
        if len(size) == 3:
            w, h, c = size
        if len(size) == 2:
            w, h = size
            c = 1
        else:
            raise Error

        res = cls(data=_bytes, height=h, width=w, encoding=BYTES, channels=c)
        file = File.from_data(sha256=sha256(_bytes).hexdigest())
        res.add_edge("file", file)
        return res