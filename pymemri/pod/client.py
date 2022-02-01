# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/pod.client.ipynb (unless otherwise specified).

__all__ = ['PodClient', 'Dog']

# Cell
from ..data.basic import *
from ..data.schema import *
from ..data.itembase import Edge, ItemBase, Item
from ..imports import *
from hashlib import sha256
from .db import DB
from .utils import *
from ..plugin.schema import *
from ..test_utils import get_ci_variables
from .api import PodAPI, PodError, DEFAULT_POD_ADDRESS, POD_VERSION

from typing import List, Union
import uuid
import urllib
from datetime import datetime
import weakref

# Cell
class PodClient:
    # Mapping from python type to schema type
    # TODO move to data.schema once schema is refactored
    TYPE_TO_SCHEMA = {
        bool: "Bool",
        str: "Text",
        int: "Integer",
        float: "Real",
        datetime: "DateTime",
    }

    def __init__(
        self,
        url=DEFAULT_POD_ADDRESS,
        version=POD_VERSION,
        database_key=None,
        owner_key=None,
        auth_json=None,
        register_base_schema=True,
        verbose=False,
        default_priority="local",
    ):
        self.verbose = verbose
        self.database_key = (
            database_key if database_key is not None else self.generate_random_key()
        )
        self.owner_key = (
            owner_key if owner_key is not None else self.generate_random_key()
        )
        self.api = PodAPI(
            database_key=self.database_key,
            owner_key=self.owner_key,
            url=url,
            version=version,
            auth_json=auth_json,
            verbose=verbose,
        )
        self.default_priority = default_priority
        self.api.test_connection()
        self.local_db = DB()
        self.registered_classes = dict()
        self.register_base_schemas()

    @classmethod
    def from_local_keys(cls, path=DEFAULT_POD_KEY_PATH, **kwargs):
        return cls(
            database_key=read_pod_key("database_key"),
            owner_key=read_pod_key("owner_key"),
            **kwargs,
        )

    @staticmethod
    def generate_random_key():
        return "".join([str(random.randint(0, 9)) for i in range(64)])

    def register_base_schemas(self):
        assert self.add_to_schema(PluginRun, CVUStoredDefinition, Account, Photo)

    def add_to_store(self, node: Item, priority=None) -> Item:
        node.ensure_id()
        priority = priority if priority is not None else self.default_priority
        return self.local_db.create(node, priority)

    def reset_local_db(self):
        self.local_db = DB()

    def get_create_dict(self, node):
        properties = node.to_json()
        properties = {k: v for k, v in properties.items() if v != []}
        return properties

    def create(self, node):
        create_dict = self.get_create_dict(node)
        try:
            result = self.api.create_item(create_dict)
            node.id = result
            self.add_to_store(node)
            node.on_sync()
            return True
        except Exception as e:
            print(e)
            return False

    def create_photo(self, photo):
        file = photo.file[0]

        # create the photo
        items_edges_success = self.bulk_action(
            create_items=[photo, file], create_edges=photo.get_edges("file")
        )
        if not items_edges_success:
            raise ValueError("Could not create file or photo item")

        return self._upload_image(photo.data)

    def _property_dicts_from_instance(self, node):
        create_items = []
        attributes = node.to_json()
        for k, v in attributes.items():
            if type(v) not in self.TYPE_TO_SCHEMA:
                raise ValueError(f"Could not add property {k} with type {type(v)}")
            value_type = self.TYPE_TO_SCHEMA[type(v)]

            create_items.append(
                {
                    "type": "ItemPropertySchema",
                    "itemType": attributes["type"],
                    "propertyName": k,
                    "valueType": value_type,
                }
            )
        return create_items

    def _property_dicts_from_type(self, item):
        create_items = []
        for property, p_type in item.get_property_types().items():
            p_type = self.TYPE_TO_SCHEMA[p_type]
            create_items.append(
                {
                    "type": "ItemPropertySchema",
                    "itemType": item.__name__,
                    "propertyName": property,
                    "valueType": p_type,
                }
            )
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

        try:
            self.api.bulk(create_items=create_items)
            return True
        except Exception as e:
            print(e)
            return False

    def _upload_image(self, img):
        if isinstance(img, np.ndarray):
            return self.upload_file(img.tobytes())
        elif isinstance(img, bytes):
            return self.upload_file(img)
        else:
            raise ValueError(f"Unknown image data type {type(img)}")

    def upload_file(self, file):
        try:
            self.api.upload_file(file)
            return True
        except PodError as e:
            # 409 = CONFLICT, file already exists
            if e.status == 409:
                return True
            return False

    def get_file(self, sha):
        return self.api.get_file(sha)

    def get_photo(self, id, size=640):
        photo = self.get(id)
        self._load_photo_data(photo, size=size)
        return photo

    def _load_photo_data(self, photo, size=None):
        if len(photo.file) > 0 and photo.data is None:
            file = self.get_file(photo.file[0].sha256)
            if file is None:
                print(
                    f"Could not load data of {photo} attached file item does not have data in pod"
                )
                return
            photo.data = file
        else:
            print(f"could not load data of {photo}, no file attached")

    def create_if_external_id_not_exists(self, node):
        if not self.external_id_exists(node):
            self.create(node)

    def external_id_exists(self, node):
        if node.externalId is None:
            return False
        existing = self.search({"externalId": node.externalId})
        return len(existing) > 0

    def create_edges(self, edges):
        return self.bulk_action(create_edges=edges)

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

    def bulk_action(
        self,
        create_items=None,
        update_items=None,
        create_edges=None,
        delete_items=None,
        partial_update=True,
        priority=None
    ):
        all_items = []
        if create_items:
            all_items += create_items
        if update_items:
            all_items += update_items

        # we need to add to local_db to not lose reference.
        if create_items is not None:
            for c in create_items:
                if not self.local_db.contains(c):
                    self.add_to_store(c, priority=priority)

        create_items = (
            [self.get_create_dict(i) for i in create_items]
            if create_items is not None
            else []
        )
        update_items = (
            [self.get_update_dict(i, partial_update=partial_update) for i in update_items]
            if update_items is not None
            else []
        )
        create_edges = (
            [self.get_create_edge_dict(i) for i in create_edges]
            if create_edges is not None
            else []
        )
        # Note: skip delete_items without id, as items that are not in pod cannot be deleted
        delete_items = (
            [item.id for item in delete_items if item.id is not None]
            if delete_items is not None
            else []
        )

        n_total = len(create_items + update_items + create_edges + delete_items)
        n = 0

        i_ci, i_ui, i_ce, i_di = 0, 0, 0, 0
        while not (
            i_ci == len(create_items)
            and i_ui == len(update_items)
            and i_ce == len(create_edges)
            and i_di == len(delete_items)
        ):
            batch_size = 0
            create_items_batch, i_ci, batch_size = self.gather_batch(
                create_items, i_ci, start_size=batch_size
            )
            update_items_batch, i_ui, batch_size = self.gather_batch(
                update_items, i_ui, start_size=batch_size
            )
            delete_items_batch, i_di, batch_size = self.gather_batch(
                delete_items, i_di, start_size=batch_size
            )
            if i_ci == len(create_items):
                create_edges_batch, i_ce, batch_size = self.gather_batch(
                    create_edges, i_ce, start_size=batch_size
                )
            else:
                create_edges_batch = []
            n_batch = len(
                create_items_batch
                + update_items_batch
                + create_edges_batch
                + delete_items_batch
            )
            n += n_batch
            print(f"BULK: Writing {n}/{n_total} items/edges")

            try:
                result = self.api.bulk(
                    create_items_batch,
                    update_items_batch,
                    create_edges_batch,
                    delete_items_batch,
                )
            except PodError as e:
                print(e)
                print("could not complete bulk action, aborting")
                return False
        print(f"Completed Bulk action, written {n} items/edges")

        for item in all_items:
            item.on_sync()
        return True

    def get_create_edge_dict(self, edge):
        return {"_source": edge.source.id, "_target": edge.target.id, "_name": edge._type}

    def create_edge(self, edge):
        edge_dict = self.get_create_edge_dict(edge)

        try:
            self.api.create_edge(edge_dict)
            return True
        except PodError as e:
            print(e)
            return False

    def get(self, id, expanded=True, include_deleted=False):
        if not expanded:
            res = self._get_item_with_properties(id)
        else:
            res = self._get_item_expanded(id)
        if res is None:
            raise ValueError(f"Item with id {id} does not exist")
        elif res.deleted and not include_deleted:
            print(f"Item with id {id} has been deleted")
            return
        return res

    def get_all_items(self):
        raise NotImplementedError()

    def filter_deleted(self, items):
        return [i for i in items if not i.deleted == True]

    def _get_item_expanded(self, id, include_deleted=False):
        item = self.get(id, expanded=False, include_deleted=include_deleted)
        edges = self.get_edges(id)
        for e in edges:
            item.add_edge(e["name"], e["item"])
        return item

    def get_edges(self, id):
        try:
            result = self.api.get_edges(id)
            for d in result:
                edge_item = self.item_from_json(d["item"])
                edge_item.on_sync()
                d["item"] = edge_item
            return result
        except PodError as e:
            print(e)
            return

    def _get_item_with_properties(self, id):
        try:
            result = self.api.get_item(str(id))
            if not len(result):
                return
            item = self.item_from_json(result[0])
            self.add_to_store(item)
            item.on_sync()
            return item
        except PodError as e:
            print(e)
            return

    def get_update_dict(self, node, partial_update=True):
        properties = node.to_json(dates=False)
        properties.pop("type", None)
        properties.pop("deleted", None)
        properties = {k: v for k, v in properties.items() if k=="id" or k in node._updated_properties}
        return properties

    def update_item(self, node, partial_update=True):
        data = self.get_update_dict(node, partial_update=partial_update)
        try:
            self.api.update_item(data)
            node.on_sync()
            return True
        except PodError as e:
            print(e)
            return False

    def exists(self, id):
        try:
            result = self.api.get_item(str(id))
            if isinstance(result, list) and len(result) > 0:
                return True
            return False
        except PodError as e:
            print(e)
            return False

    def search_paginate(self, fields_data, limit=50, include_edges=True, add_to_local_db: bool = True, priority = None):
        if "ids" in fields_data:
            raise NotImplementedError("Searching by multiple IDs is not implemented for paginated search.")

        extra_fields = {"[[edges]]": {}} if include_edges else {}
        query = {**fields_data, **extra_fields}

        try:
            for page in self.api.search_paginate(query, limit):
                result = [self._item_from_search(item, add_to_local_db=add_to_local_db, priority=priority) for item in page]
                yield self.filter_deleted(result)
        except PodError as e:
            print(e)

    def search(self, fields_data, include_edges: bool = True, add_to_local_db: bool = True, priority = None):
        extra_fields = {"[[edges]]": {}} if include_edges else {}
        query = {**fields_data, **extra_fields}

        # Special key "ids" for searching a list of ids.
        # Requires /bulk search instead of /search.
        if "ids" in query:
            ids = query.pop("ids")
            bulk_query = [{"id": uid, **query} for uid in ids]
            try:
                result = self.api.bulk(search=bulk_query)["search"]
            except PodError as e:
                print(e)

            result = [item for sublist in result for item in sublist]
        else:
            try:
                result = self.api.search(query)
            except PodError as e:
                print(e)

        result = [self._item_from_search(item, add_to_local_db=add_to_local_db, priority=priority) for item in result]
        return self.filter_deleted(result)

    def _item_from_search(self, item_json: dict, add_to_local_db: bool = True, priority=None):
        # search returns different fields w.r.t. edges compared to `get` api,
        # different method to keep `self.get` clean.
        item = self.item_from_json(item_json, add_to_local_db=add_to_local_db, priority=priority)
        item.on_sync()

        for edge_json in item_json.get("[[edges]]", []):
            edge_name = edge_json["_edge"]
            try:
                edge_item = self.item_from_json(edge_json["_item"], add_to_local_db=add_to_local_db, priority=priority)
                edge_item.on_sync()
                item.add_edge(edge_name, edge_item)
            except Exception as e:
                print(f"Could not attach edge {edge_json['_item']} to {item}")
                print(e)
                continue
        return item

    def search_last_added(self, type=None, with_prop=None, with_val=None):
        query = {"_limit": 1, "_sortOrder": "Desc"}
        if type is not None:
            query["type"] = type
        if with_prop is not None:
            query[f"{with_prop}=="] = with_val
        return self.search(query)[0]


    def item_from_json(
        self,
        json: dict,
        add_client_ref: bool = False,
        add_to_local_db: bool = True,
        priority = None,
    ) -> Item:

        plugin_class = json.get("pluginClass", None)
        plugin_package = json.get("pluginPackage", None)
        item_class = get_constructor(
            json["type"],
            plugin_class,
            plugin_package=plugin_package,
            extra=self.registered_classes,
        )

        new_item = item_class.from_json(json)
        if add_to_local_db:
            new_item = self.add_to_store(new_item, priority=priority)
        if add_client_ref:
            new_item._client = weakref.ref(self)
        return new_item

    def get_properties(self, expanded):
        properties = copy(expanded)
        if ALL_EDGES in properties:
            del properties[ALL_EDGES]
        return properties

    def send_email(self, to, subject="", body=""):
        try:
            self.api.send_email(to, subject, body)
            print(f"succesfully sent email to {to}")
            return True
        except PodError as e:
            print(e)
            return False

    def sync(self, priority: str = "newest"):
        all_items = list(self.local_db.nodes.values())
        all_ids = set(self.local_db.nodes.keys())

        create_items = []
        update_items = []
        create_edges = []

        # Add items from sync store
        for item in all_items:
            if isinstance(item, File) or isinstance(item, Photo):
                continue
            if item._in_pod:
                update_items.append(item)
            else:
                create_items.append(item)

            # Add all edges where src and tgt exist
            for edge in item._new_edges:
                if edge.target.id in all_ids:
                    create_edges.append(edge)
                else:
                    warnings.warn(f"Could not sync `{edge._type}` for {item}: edge target missing in sync.")

        update_ids = [item.id for item in update_items]
        existing_items = self.search({"ids": update_ids}, add_to_local_db=True, priority=priority)
        existing_items = {item.id: item for item  in existing_items}

        assert self.bulk_action(
            create_items=create_items,
            update_items=update_items,
            create_edges=create_edges,
            priority=priority
        )
        return True


# Cell
class Dog(Item):
    properties = Item.properties + ["name", "age", "bites", "weight"]

    def __init__(self, name: str=None, age: int=None, bites: bool=False, weight: float=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.age = age
        self.bites = bites
        self.weight = weight