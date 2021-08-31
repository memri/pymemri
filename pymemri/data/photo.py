# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/data.photo.ipynb (unless otherwise specified).

__all__ = ['show_images', 'get_size', 'resize', 'get_height_width_channels', 'Photo', 'IPhoto']

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
# An image file.
class Photo(Item):
    def __init__(self, dateAccessed=None, dateCreated=None, dateModified=None, deleted=None,
                 externalId=None, itemDescription=None, starred=None, version=None, id=None, importJson=None,
                 bitrate=None, duration=None, endTime=None, fileLocation=None, startTime=None, caption=None,
                 exifData=None, name=None, height=None, width=None, channels=None, changelog=None, label=None,
                 genericAttribute=None, measure=None, sharedWith=None, file=None, includes=None, thumbnail=None):
        super().__init__(dateAccessed=dateAccessed, dateCreated=dateCreated, dateModified=dateModified,
                         deleted=deleted, externalId=externalId, itemDescription=itemDescription, starred=starred,
                         version=version, id=id, importJson=importJson, changelog=changelog, label=label,
                         genericAttribute=genericAttribute, measure=measure, sharedWith=sharedWith)
        self.bitrate = bitrate
        self.duration = duration
        self.endTime = endTime
        self.fileLocation = fileLocation
        self.startTime = startTime
        self.caption = caption
        self.exifData = exifData
        self.name = name
        self.height = height
        self.width = width
        self.channels = channels
        self.file = file if file is not None else []
        self.includes = includes if includes is not None else []
        self.thumbnail = thumbnail if thumbnail is not None else []

    @classmethod
    def from_json(cls, json):
        all_edges = json.get("allEdges", None)
        dateAccessed = json.get("dateAccessed", None)
        dateCreated = json.get("dateCreated", None)
        dateModified = json.get("dateModified", None)
        deleted = json.get("deleted", None)
        externalId = json.get("externalId", None)
        itemDescription = json.get("itemDescription", None)
        starred = json.get("starred", None)
        version = json.get("version", None)
        id = json.get("id", None)
        importJson = json.get("importJson", None)
        bitrate = json.get("bitrate", None)
        duration = json.get("duration", None)
        endTime = json.get("endTime", None)
        fileLocation = json.get("fileLocation", None)
        startTime = json.get("startTime", None)
        caption = json.get("caption", None)
        exifData = json.get("exifData", None)
        name = json.get("name", None)
        height = json.get("height", None)
        width = json.get("width", None)
        channels = json.get("channels", None)

        changelog = []
        label = []
        genericAttribute = []
        measure = []
        sharedWith = []
        file = []
        includes = []
        thumbnail = []

        if all_edges is not None:
            for edge_json in all_edges:
                edge = Edge.from_json(edge_json)
                if edge._type == "changelog" or edge._type == "~changelog":
                    changelog.append(edge)
                elif edge._type == "label" or edge._type == "~label":
                    label.append(edge)
                elif edge._type == "genericAttribute" or edge._type == "~genericAttribute":
                    genericAttribute.append(edge)
                elif edge._type == "measure" or edge._type == "~measure":
                    measure.append(edge)
                elif edge._type == "sharedWith" or edge._type == "~sharedWith":
                    sharedWith.append(edge)
                elif edge._type == "file" or edge._type == "~file":
                    file.append(edge)
                elif edge._type == "includes" or edge._type == "~includes":
                    includes.append(edge)
                elif edge._type == "thumbnail" or edge._type == "~thumbnail":
                    thumbnail.append(edge)

        res = cls(dateAccessed=dateAccessed, dateCreated=dateCreated, dateModified=dateModified,
                  deleted=deleted, externalId=externalId, itemDescription=itemDescription, starred=starred,
                  version=version, id=id, importJson=importJson, bitrate=bitrate, duration=duration,
                  endTime=endTime, fileLocation=fileLocation, startTime=startTime, caption=caption, exifData=exifData,
                  name=name, height=height, width=width, channels=channels, changelog=changelog, label=label,
                  genericAttribute=genericAttribute, measure=measure, sharedWith=sharedWith, file=file,
                  includes=includes, thumbnail=thumbnail)
        for e in res.get_all_edges(): e.source = res
        return res

# Cell
NUMPY, BYTES = "numpy", "bytes"

# Cell
class IPhoto(Photo):
    properties = Item.properties + [
        "service",
        "identifier",
        "secret",
        "code",
        "handle",
        "refreshToken",
        "errorMessage",
        "accessToken",
        "displayName"
    ]
    edges = Item.edges + ['belongsTo', 'contact']

    def __init__(self, data=None, embedding=None,path=None, encoding=None, *args, **kwargs):
        self.private = ["data", "embedding", "path"]
        super().__init__(*args, **kwargs)
        self.data=data
        self.embedding=embedding
        self.path=path
        self.encoding=encoding

    def show(self):
        fig,ax = plt.subplots(1)
        fig.set_figheight(15)
        fig.set_figwidth(15)
        ax.axis('off')
        imshow(self.data[:,:,::-1])
        fig.set_size_inches((6,6))
        plt.show()

    def draw_boxes(self, boxes):
        print(f"Plotting {len(boxes)} face boundingboxes")
        fig,ax = plt.subplots(1)
        fig.set_figheight(15)
        fig.set_figwidth(15)
        ax.axis('off')

        # Display the image
        ax.imshow(self.data[:,:,::-1])

        ps = []
        # Create a Rectangle patch
        for b in boxes:
            rect = self.box_to_rect(b)
            ax.add_patch(rect)
            ps.append(rect)
        fig.set_size_inches((6,6))
        plt.show()

    def get_crop(self, box, landmark=None):
        b = [max(0, int(x)) for x in box]
        if landmark is not None:
            return face_align.norm_crop(self.data, landmark=landmark)
        else:
            return self.data[b[1]:b[3], b[0]:b[2], :]

    def get_crops(self, boxes, landmarks=None):
        crops = []
        if landmarks is None:
            print("you are getting unnormalized crops, which are lower quality for recognition")
        for i, b in enumerate(boxes):
            crop = self.get_crop(b, landmarks[i] if landmarks is not None else None)
            crops.append(crop)
        return crops

    def plot_crops(self, boxes, landmarks=None):
        crops = self.get_crops(boxes, landmarks)
        show_images(crops, cols=3)

    @classmethod
    def from_data(cls,*args, **kwargs):
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
        if size is not None: data = resize(data, size)
        h,w,c = get_height_width_channels(data)
        res = cls(data=data, height=h, width=w, channels=c, encoding=NUMPY, *args, **kwargs)
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
            w,h = size
            c=1
        else:
            raise Error

        res = cls(data=_bytes, height=h, width=w, encoding=BYTES, channels=c)
        file = File.from_data(sha256=sha256(_bytes).hexdigest())
        res.add_edge("file", file)
        return res

    @staticmethod
    def box_to_rect(box):
        x = box[0]
        y = box[1]
        w = box[2]-box[0]
        h = box[3]-box[1]
        return patches.Rectangle((x,y),w,h, linewidth=2,edgecolor='r',facecolor='none')