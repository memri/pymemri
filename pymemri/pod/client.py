# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/pod.client.ipynb (unless otherwise specified).

__all__ = ['DEFAULT_POD_ADDRESS', 'POD_VERSION', 'PodClient', 'Dog']

# Cell
from ..data.basic import *
from ..data.schema import *
from ..data.itembase import Edge, ItemBase, Item
from ..data.photo import Photo, NUMPY, BYTES
from ..imports import *
from hashlib import sha256
from .db import DB
from .utils import *
from ..plugin.schema import *

from typing import List, Union
import uuid
import urllib
from datetime import datetime

# Cell
DEFAULT_POD_ADDRESS = "http://localhost:3030"
POD_VERSION = "v4"

# Cell
class PodClient:
    # Mapping from python type to schema type
    # TODO move to data.schema once schema is refactored
    TYPE_TO_SCHEMA = {
        bool: "Bool",
        str: "Text",
        int: "Integer",
        float: "Real",
        datetime: "DateTime"
    }

    def __init__(self, url=DEFAULT_POD_ADDRESS, version=POD_VERSION, database_key=None, owner_key=None,
                 auth_json=None, verbose=False, register_base_schema=True):
        self.verbose = verbose
        self.url = url
        self.version = POD_VERSION
        self.test_connection(verbose=self.verbose)

        self.database_key=database_key if database_key is not None else self.generate_random_key()
        self.owner_key=owner_key if owner_key is not None else self.generate_random_key()
        self.base_url = f"{url}/{version}/{self.owner_key}"
        self.auth_json = {"type":"ClientAuth","databaseKey":self.database_key} if auth_json is None \
                          else {**{"type": "PluginAuth"}, **auth_json}

        self.local_db = DB()
        self.registered_classes=dict()
        self.register_base_schemas()

    @classmethod
    def from_local_keys(cls, path=DEFAULT_POD_KEY_PATH, **kwargs):
        return cls(database_key=read_pod_key("database_key"), owner_key=read_pod_key("owner_key"), **kwargs)

    @staticmethod
    def generate_random_key():
        return "".join([str(random.randint(0, 9)) for i in range(64)])

    def register_base_schemas(self):

        assert self.add_to_schema(
            PluginRun, CVUStoredDefinition, Account, Photo
        )

    def test_connection(self, verbose=True):
        try:
            res = requests.get(self.url)
            if verbose: print("Succesfully connected to pod")
            return True
        except requests.exceptions.RequestException as e:
            print("Could no connect to backend")
            return False

    def add_to_db(self, node):
            existing = self.local_db.get(node.id)
            if existing is None and node.id is not None:
                self.local_db.add(node)

    def reset_local_db(self):
        self.local_db = DB()

    def get_create_dict(self, node):
        properties = node.to_json()
        properties = {k:v for k, v in properties.items() if v != []}
        return properties

    def create(self, node):
        create_dict = self.get_create_dict(node)
        try:
            body = {"auth": self.auth_json, "payload": create_dict}

            result = requests.post(f"{self.base_url}/create_item", json=body)
            if result.status_code != 200:
                print(result, result.content)
                return False
            else:
                id = result.json()
                node.id = id
                self.add_to_db(node)
                return True
        except requests.exceptions.RequestException as e:
            print(e)
            return False

    def create_photo(self, photo):
        # create the file
        file_succes = self.create_photo_file(photo)
        if file_succes == False:
            raise ValueError("Could not create file")
        # create the photo
        return self.bulk_action(create_items=[photo], create_edges=photo.get_edges("file"))


    def _property_dicts_from_instance(self, node):
        create_items = []
        attributes = node.to_json()
        for k, v in attributes.items():
            if type(v) not in self.TYPE_TO_SCHEMA:
                raise ValueError(f"Could not add property {k} with type {type(v)}")
            value_type = self.TYPE_TO_SCHEMA[type(v)]

            create_items.append({
                "type": "ItemPropertySchema", "itemType": attributes["type"],
                "propertyName": k, "valueType": value_type
            })
        return create_items


    def _property_dicts_from_type(self, item):
        create_items = []
        for property, p_type in item.get_property_types().items():
            p_type = self.TYPE_TO_SCHEMA[p_type]
            create_items.append({
                "type": "ItemPropertySchema", "itemType": item.__name__,
                "propertyName": property, "valueType": p_type
            })
        return create_items


    def add_to_schema(self, *items: List[Union[object, type]]):
        create_items = []

        for item in items:
            if isinstance(item, type):
                property_dicts = self._property_dicts_from_type(item)
            else:
                property_dicts = self._property_dicts_from_instance(item)
                item = type(item)
            create_items.extend(property_dicts)
            self.registered_classes[item.__name__] = item

        body = {
            "auth": self.auth_json, "payload": {"createItems": create_items}
        }

        try:
            result = requests.post(f"{self.base_url}/bulk", json=body)
            if result.status_code != 200:
                print(result, result.content)
                return False
        except requests.exceptions.RequestException as e:
            print(e)
            return False
        return True

    def create_photo_file(self, photo):
        file = photo.file[0]
        self.create(file)
        return self._upload_image(photo.data)

    def _upload_image(self, img):
        if isinstance(img, np.ndarray):
            return self.upload_file(img.tobytes())
        elif isinstance(img, bytes):
            return self.upload_file(img)
        else:
            raise ValueError(f"Unknown image data type {type(img)}")

    def upload_file(self, file):
        # TODO: currently this only works for numpy images
        if self.auth_json.get("type") == "PluginAuth":
            # alternative file upload for plugins, with different authentication
            return self.upload_file_b(file)
        else:
            try:
                sha = sha256(file).hexdigest()
                result = requests.post(f"{self.base_url}/upload_file/{self.database_key}/{sha}", data=file)
                if result.status_code in [200, 409]: # 409 = CONFLICT, file already exists
                    return True
                else:
                    print(result, result.content)
                    return False
            except requests.exceptions.RequestException as e:
                print(e)
                return False

    def upload_file_b(self, file):
        try:
            sha = sha256(file).hexdigest()
            auth = urllib.parse.quote(json.dumps(self.auth_json))
            result = requests.post(f"{self.base_url}/upload_file_b/{auth}/{sha}", data=file)
            if result.status_code in [200, 409]: # 409 = CONFLICT, file already exists
                return True
            else:
                print(result, result.content)
                return False
        except requests.exceptions.RequestException as e:
            print(e)
            return False

    def get_file(self, sha):
        # TODO: currently this only works for numpy images
        try:
            body= {"auth": self.auth_json,
                   "payload": {"sha256": sha}}
            result = requests.post(f"{self.base_url}/get_file", json=body)
            if result.status_code != 200:
                print(result, result.content)
                return None
            else:
                return result.content
        except requests.exceptions.RequestException as e:
            print(e)
            return None

    def get_photo(self, id, size=640):
        photo = self.get(id)
        self._load_photo_data(photo, size=size)
        return photo

    def _load_photo_data(self, photo, size=None):
        if len(photo.file) > 0 and photo.data is None:
            file = self.get_file(photo.file[0].sha256)
            if file is None:
                print(f"Could not load data of {photo} attached file item does not have data in pod")
                return
            if photo.encoding == NUMPY:
                data = np.frombuffer(file, dtype=np.uint8)
                c = photo.channels
                shape = (photo.height,photo.width, c) if c is not None and c > 1 else (photo.height, photo.width)
                data = data.reshape(shape)
                if size is not None: data = resize(data, size)
                photo.data = data
                return
            elif photo.encoding == BYTES:
                photo.data = file
                return
            else:
                raise ValueError("Unsupported encoding")
        print(f"could not load data of {photo}, no file attached")

    def create_if_external_id_not_exists(self, node):
        if not self.external_id_exists(node):
            self.create(node)

    def external_id_exists(self, node):
        if node.externalId is None: return False
        existing = self.search({"externalId": node.externalId})
        return len(existing) > 0

    def create_edges(self, edges):
        """Create edges between nodes, edges should be of format:
           [{"_type": "friend", "_source": 1, "_target": 2}]"""
        return self.bulk_action(create_edges=edges)

#         create_edges = []
#         for e in edges:
#             src, target = e.source.id, e.target.id

#             if src is None or target is None:
#                 print(f"Could not create edge {e} missing source or target id")
#                 return False
#             data = {"_source": src, "_target": target, "_name": e._type}
#             if e.label is not None: data[LABEL] = e.label
#             if e.sequence is not None: data[SEQUENCE] = e.sequence

#             if e.reverse:
#                 data2 = copy(data)
#                 data2["_source"] = target
#                 data2["_target"] = src
#                 data2["_name"] = "~" + data2["_name"]
#                 create_edges.append(data2)

#             create_edges.append(data)

#         return self.bulk_action(create_items=[], update_items=[],create_edges=create_edges)

    def delete_items(self, items):
        return self.bulk_action(delete_items=items)

    def delete_all(self):
        items = self.get_all_items()
        self.delete_items(items)

    @staticmethod
    def gather_batch(items, start_idx, start_size=0, max_size=5000000):
        idx = start_idx
        total_size = start_size
        batch_items = []
        for i, x in enumerate(items):
            if i < idx:
                continue
            elif len(str(x)) > max_size:
                idx = i + 1
                print("Could not add item: Item exceeds max item size")
            elif total_size + len(str(x)) < max_size:
                batch_items.append(x)
                total_size += len(str(x))
                idx = i + 1
            else:
                break
        return batch_items, idx, total_size

    def bulk_action(self, create_items=None, update_items=None, create_edges=None, delete_items=None):
        # we need to set the id to not lose the reference
        if create_items is not None:
            for c in create_items:
                if c.id is None: c.id = uuid.uuid4().hex
        create_items = [self.get_create_dict(i) for i in create_items] if create_items is not None else []
        update_items = [self.get_update_dict(i) for i in update_items] if update_items is not None else []
        create_edges = [self.get_create_edge_dict(i) for i in create_edges] if create_edges is not None else []
        # Note: skip delete_items without id, as items that are not in pod cannot be deleted
        delete_items = [item.id for item in delete_items if item.id is not None] if delete_items is not None else []

        n_total = len(create_items + update_items + create_edges + delete_items)
        n=0

        i_ci, i_ui, i_ce, i_di = 0,0,0,0
        while not( i_ci == len(create_items) and i_ui == len(update_items) and i_ce == len(create_edges) and i_di == len(delete_items)):
            batch_size=0
            create_items_batch, i_ci, batch_size = self.gather_batch(create_items, i_ci, start_size=batch_size)
            update_items_batch, i_ui, batch_size = self.gather_batch(update_items, i_ui, start_size=batch_size)
            delete_items_batch, i_di, batch_size = self.gather_batch(delete_items, i_di, start_size=batch_size)
            if i_ci == len(create_items):
                create_edges_batch, i_ce, batch_size = self.gather_batch(create_edges, i_ce, start_size=batch_size)
            else:
                create_edges_batch = []
            n_batch = len(create_items_batch+update_items_batch+create_edges_batch+delete_items_batch)
            n+=n_batch
            print(f"BULK: Writing {n}/{n_total} items/edges")
            succes = self._bulk_action(create_items_batch, update_items_batch, create_edges_batch, delete_items_batch)
            if not succes:
                print("could not complete bulk aciton, aborting")
                return False
        print(f"Completed Bulk action, written {n} items/edges")
        return True

    def _bulk_action(self, create_items=None, update_items=None, create_edges=None, delete_items=None):
        json_data = {
            "auth": self.auth_json,
            "payload": {
                "createItems": create_items, "updateItems": update_items,
                "createEdges": create_edges, "deleteItems": delete_items
            }
        }

        try:
            result = requests.post(f"{self.base_url}/bulk",
                                   json=json_data)
            if result.status_code != 200:
                if "UNIQUE constraint failed" in str(result.content):
                    print(result.status_code, result.content, "Failed bulk update")
                else:
                    print(result, result.content)
                return False
            else:
                return True
        except requests.exceptions.RequestException as e:
            print(e)
            return False

    def get_create_edge_dict(self, edge):
        return {"_source": edge.source.id, "_target": edge.target.id, "_name": edge._type}

    def create_edge(self, edge):
        payload = self.get_create_edge_dict(edge)
        body = {"auth": self.auth_json,
                "payload": payload}

        try:
            result = requests.post(f"{self.base_url}/create_edge", json=body)
            if result.status_code != 200:
                print(result, result.content)
                return False
            else:
                return True
        except requests.exceptions.RequestException as e:
            print(e)
            return False

        return self.create_edges([edge])

    def get(self, id, expanded=True):
        if not expanded:
            res = self._get_item_with_properties(id)
        else:
            res = self._get_item_expanded(id)
        if res is None:
            raise ValueError(f"Item with id {id} does not exist")

        elif res.deleted == True:
            print(f"Item with id {id} does not exist anymore")
            return None
        else:
            return res

    def get_all_items(self):
        raise NotImplementedError()
        try:
            body = {  "databaseKey": self.database_key, "payload":None}
            result = requests.post(f"{self.base_url}/get_all_items", json=body)
            if result.status_code != 200:
                print(result, result.content)
                return None
            else:
                json = result.json()
                res =  [self.item_from_json(x) for x in json]
                return self.filter_deleted(res)

        except requests.exceptions.RequestException as e:
            print(e)
            return None

    def filter_deleted(self, items):
        return [i for i in items if not i.deleted == True]

    def _get_item_expanded(self, id):
        item = self.get(id, expanded=False)
        edges = self.get_edges(id)
        for e in edges:
            item.add_edge(e["name"], e["item"])
        return item

    def get_edges(self, id):
        body = {"payload": {"item": str(id),
                            "direction": "Outgoing",
                            "expandItems": True},
                "auth": self.auth_json}

        try:
            result = requests.post(f"{self.base_url}/get_edges", json=body)
            if result.status_code != 200:
                print(result, result.content)
                return None
            else:
                json = result.json()
                for d in json:
                    d["item"] = self.item_from_json(d["item"])
                return json
        except requests.exceptions.RequestException as e:
            print(e)
            return None

    def _get_item_with_properties(self, id):
        try:
            body = {"auth": self.auth_json,
                    "payload": str(id)}
            result = requests.post(f"{self.base_url}/get_item", json=body)
            if result.status_code != 200:
                print(result, result.content)
                return None
            else:
                json = result.json()
                if json == []:
                    return None
                else:
                    res =  self.item_from_json(json[0])
                    return res
        except requests.exceptions.RequestException as e:
            print(e)
            return None

    def get_update_dict(self, node):
        properties = node.to_json(dates=False)
        properties.pop("type", None)
        properties.pop("deleted", None)
        return properties

    def update_item(self, node):
        data = self.get_update_dict(node)
        body = {"payload": data,
                "auth": self.auth_json}
        try:
            result = requests.post(f"{self.base_url}/update_item",
                                  json=body)
            if result.status_code != 200:
                print(result, result.content)
        except requests.exceptions.RequestException as e:
            print(e)

    def exists(self, id):
        try:
            body = {"auth": self.auth_json,
                    "payload": str(id)}
            result = requests.post(f"{self.base_url}/get_item", json=body)
            if result.status_code != 200:
                print(result, result.content)
                return False
            else:
                json = result.json()
                if isinstance(json, list) and len(json) > 0:
                    return True

        except requests.exceptions.RequestException as e:
            print(e)
            return None

    def search(self, fields_data, include_edges: bool = True):
        extra_fields = {'[[edges]]': {}} if include_edges else {}
        body = {"payload": {**fields_data, **extra_fields},
                "auth": self.auth_json}
        try:
            result = requests.post(f"{self.base_url}/search", json=body)
            json =  result.json()

            res = [self._item_from_search(item) for item in json]
            return self.filter_deleted(res)
        except requests.exceptions.RequestException as e:
            return None


    def _item_from_search(self, item_json: dict):
        # search returns different fields w.r.t. edges compared to `get` api,
        # different method to keep `self.get` clean.
        item = self.item_from_json(item_json)

        for edge_json in item_json.get("[[edges]]", []):
            edge_name = edge_json["_edge"]
            try:
                edge_item = self.item_from_json(edge_json["_item"])
                item.add_edge(edge_name, edge_item)
            except Exception as e:
                continue
        return item

    def search_last_added(self, type=None, with_prop=None, with_val=None):
        query = {"_limit": 1, "_sortOrder": "Desc"}
        if type is not None:
            query["type"] = type
        if with_prop is not None:
            query[f"{with_prop}=="] = with_val

        return self.search(query)[0]

    def item_from_json(self, json):
        plugin_class = json.get("pluginClass", None)
        plugin_package = json.get("pluginPackage", None)

        constructor = get_constructor(json["type"], plugin_class, plugin_package=plugin_package,
                                      extra=self.registered_classes)
        new_item = constructor.from_json(json)
        existing = self.local_db.get(new_item.id)
        # TODO: cleanup
        if existing is not None:
            if not existing.is_expanded() and new_item.is_expanded():
                for edge_name in new_item.get_all_edge_names():
                    edges = new_item.get_edges(edge_name)
                    for e in edges:
                        e.source = existing
                    existing.__setattr__(edge_name, edges)

            for prop_name in new_item.get_property_names():
                existing.__setattr__(prop_name, new_item.__getattribute__(prop_name))
            return existing
        else:
            return new_item

    def get_properties(self, expanded):
        properties = copy(expanded)
        if ALL_EDGES in properties: del properties[ALL_EDGES]
        return properties

    def send_email(self, to, subject="", body=""):
        body = {"payload": {"to": to,
                            "subject": subject,
                            "body": body
                           },
                "auth": self.auth_json}
        try:
            result = requests.post(f"{self.base_url}/send_email", json=body)
            if result.status_code == 200:
                print(f"succesfully sent email to {to}")
            else:
                print(f"could not send email {result.content}")
        except requests.exceptions.RequestException as e:
            print(e)
            return None

# Cell
class Dog(Item):
    properties = Item.properties + ["name", "age", "bites", "weight"]
    edges = Item.edges
    def __init__(self, name: str=None, age: int=None, bites: bool=False, weight: float=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.age = age
        self.bites = bites
        self.weight = weight