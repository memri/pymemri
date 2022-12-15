import random
import warnings
from datetime import datetime
from threading import Thread
from typing import Any, Dict, List, Optional, Type, Union

import numpy as np
from loguru import logger

from pymemri.data.schema.itembase import ItemBase

from ..data.schema import Account, File, Photo, PluginRun, get_schema_cls
from .api import DEFAULT_POD_ADDRESS, POD_VERSION, PodAPI, PodError
from .db import DB, Priority
from .graphql_utils import GQLQuery
from .utils import DEFAULT_POD_KEY_PATH, read_pod_key


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
        default_priority=Priority.local,
        create_account=True,
    ):
        self.verbose = verbose
        self.database_key = database_key if database_key is not None else self.generate_random_key()
        self.owner_key = owner_key if owner_key is not None else self.generate_random_key()
        self.api = PodAPI(
            database_key=self.database_key,
            owner_key=self.owner_key,
            url=url,
            version=version,
            auth_json=auth_json,
            verbose=verbose,
        )

        self.default_priority = Priority(default_priority)

        if create_account:
            self.create_account()

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

    def create_account(self):
        try:
            self.api.create_account()
        except PodError as e:
            logger.warning(e)

    def register_base_schemas(self):
        result = self.add_to_schema(PluginRun, Account)
        if not result:
            raise ValueError("Could not register base schemas")

    def add_to_store(self, item: ItemBase, priority: Priority = None) -> ItemBase:
        item.create_id_if_not_exists()
        priority = priority if priority is not None else self.default_priority
        return self.local_db.merge(item, priority)

    def reset_local_db(self):
        self.local_db = DB()

    def create(self, item):
        self.add_to_store(item)
        try:
            result = self.api.create_item(item.to_json())
            item.id = result
            item.reset_local_sync_state()
            if getattr(item, "requires_client_ref", False):
                item._client = self
            return True
        except Exception as e:
            logger.error(e)
            return False

    def create_photo(self, photo, asyncFlag=True):
        file = photo.file[0]

        # create the photo
        items_edges_success = self.bulk_action(
            create_items=[photo, file], create_edges=photo.get_edges("file")
        )
        if not items_edges_success:
            raise ValueError("Could not create file or photo item")

        return self._upload_image(photo.data, asyncFlag=asyncFlag)

    def add_to_schema(self, *items: List[Union[object, type]]):
        create_items = []
        for item in items:
            if not (isinstance(item, ItemBase) or issubclass(item, ItemBase)):
                raise ValueError(f"{item} is not an instance or subclass of Item")
            create_items.extend(item.pod_schema())

        self.api.bulk(create_items=create_items)
        for item in items:
            item_cls = type(item) if isinstance(item, ItemBase) else item
            self.registered_classes[item.__name__] = item_cls
        return True

    def _upload_image(self, img, asyncFlag=True, callback=None):
        if isinstance(img, np.ndarray):
            return self.upload_file(img.tobytes(), asyncFlag=asyncFlag, callback=callback)
        elif isinstance(img, bytes):
            return self.upload_file(img, asyncFlag=asyncFlag, callback=callback)
        else:
            raise ValueError(f"Unknown image data type {type(img)}")

    def upload_file(self, file, asyncFlag=True, callback=None):
        if asyncFlag:
            return self.upload_file_async(file, callback=callback)
        try:
            self.api.upload_file(file)
            return True
        except PodError as e:
            # 409 = CONFLICT, file already exists
            if e.status == 409:
                return True
            return False

    def upload_file_async(self, file, callback=None):
        def thread_fn(file, callback):
            result = self.upload_file(file, asyncFlag=False)
            if callback:
                callback(result)

        Thread(target=thread_fn, args=(file, callback)).start()
        return True

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
                logger.error(
                    f"Could not load data of {photo} attached file item does not have data in pod"
                )
                return
            photo.data = file
        else:
            logger.error(f"could not load data of {photo}, no file attached")

    def create_if_external_id_not_exists(self, item):
        if not self.external_id_exists(item):
            self.create(item)

    def external_id_exists(self, item):
        if item.externalId is None:
            return False
        existing = self.search({"externalId": item.externalId})
        return len(existing) > 0

    def create_edges(self, edges):
        return self.bulk_action(create_edges=edges)

    def delete_items(self, items):
        return self.bulk_action(delete_items=items)

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
                logger.error("Could not add item: Item exceeds max item size")
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
        priority=None,
    ):
        priority = Priority(priority) if priority else None

        all_items = []
        if create_items:
            all_items += create_items
        if update_items:
            all_items += update_items

        # we need to add to local_db to not lose reference.
        if create_items is not None:
            for c in create_items:
                if getattr(c, "requires_client_ref", False):
                    c._client = self
                if not self.local_db.contains(c):
                    self.add_to_store(c, priority=priority)

        create_items = [item.to_json() for item in create_items] if create_items is not None else []
        update_items = (
            [self.get_update_dict(i, partial_update=partial_update) for i in update_items]
            if update_items is not None
            else []
        )
        create_edges = (
            [self.get_create_edge_dict(i) for i in create_edges] if create_edges is not None else []
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
                create_items_batch + update_items_batch + create_edges_batch + delete_items_batch
            )
            n += n_batch
            logger.info(f"BULK: Writing {n}/{n_total} items/edges")

            try:
                result = self.api.bulk(
                    create_items_batch,
                    update_items_batch,
                    create_edges_batch,
                    delete_items_batch,
                )
            except PodError as e:
                logger.error(f"could not complete bulk action {e}, aborting")
                return False
        logger.info(f"Completed Bulk action, written {n} items/edges")

        for item in all_items:
            item.reset_local_sync_state()
        return True

    def get_create_edge_dict(self, edge):
        return {
            "_source": edge.source.id,
            "_target": edge.target.id,
            "_name": edge.name,
        }

    def create_edge(self, edge):
        edge_dict = self.get_create_edge_dict(edge)

        try:
            self.api.create_edge(edge_dict)
            return True
        except PodError as e:
            logger.error(e)
            return False

    def get(self, id, expanded=True, include_deleted=False):
        if not expanded:
            res = self._get_item_with_properties(id)
        else:
            res = self._get_item_expanded(id)
        if res is None:
            raise ValueError(f"Item with id {id} does not exist")
        elif res.deleted and not include_deleted:
            logger.info(f"Item with id {id} has been deleted")
            return
        return res

    def filter_deleted(self, items):
        return [i for i in items if not i.deleted == True]

    def _get_item_expanded(self, id):
        item = self._get_item_with_properties(id)
        edges = self.get_edges(id)
        for e in edges:
            if e["name"] in item.edges:
                item.add_edge(e["name"], e["item"])
            else:
                logger.debug(f"Could not add edge {e['name']}: Edge is not defined on Item.")
        return item

    def get_edges(self, id):
        try:
            result = self.api.get_edges(id)
            for edge_name in result:
                edge_item = self.item_from_json(edge_name["item"])
                edge_item.reset_local_sync_state()
                edge_name["item"] = edge_item
            return result
        except PodError as e:
            logger.error(e)
            return

    def _get_item_with_properties(self, id):
        try:
            result = self.api.get_item(str(id))
            if not len(result):
                return
            item = self.item_from_json(result[0])
            item.reset_local_sync_state()
            return item
        except PodError as e:
            logger.error(e)
            return

    def get_update_dict(self, item: ItemBase, partial_update: bool = True):
        properties = item.property_dict()
        properties.pop("deleted", None)
        if partial_update:
            properties = {
                k: v for k, v in properties.items() if k == "id" or k in item._updated_properties
            }
        return properties

    def update_item(self, item, partial_update=True):
        data = self.get_update_dict(item, partial_update=partial_update)
        try:
            self.api.update_item(data)
            item.reset_local_sync_state()
            return True
        except PodError as e:
            logger.error(e)
            return False

    def exists(self, id):
        try:
            result = self.api.get_item(str(id))
            if isinstance(result, list) and len(result) > 0:
                return True
            return False
        except PodError as e:
            logger.error(e)
            return False

    def search_paginate(
        self,
        fields_data,
        limit=50,
        include_edges=True,
        add_to_local_db: bool = True,
        priority=None,
    ):
        priority = Priority(priority) if priority else None

        if "ids" in fields_data:
            raise NotImplementedError(
                "Searching by multiple IDs is not implemented for paginated search."
            )

        extra_fields = {"[[edges]]": {}} if include_edges else {}
        query = {**fields_data, **extra_fields}

        try:
            for page in self.api.search_paginate(query, limit):
                result = [
                    self._item_from_search(item, add_to_local_db=add_to_local_db, priority=priority)
                    for item in page
                ]
                yield self.filter_deleted(result)
        except PodError as e:
            logger.error(e)

    def search(
        self,
        fields_data,
        include_edges: bool = True,
        add_to_local_db: bool = True,
        priority=None,
    ):
        priority = Priority(priority) if priority else None

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
                logger.error(e)

            result = [item for sublist in result for item in sublist]
        else:
            try:
                result = self.api.search(query)
            except PodError as e:
                logger.error(e)

        result = [
            self._item_from_search(item, add_to_local_db=add_to_local_db, priority=priority)
            for item in result
        ]
        return self.filter_deleted(result)

    def _item_from_search(self, item_json: dict, add_to_local_db: bool = True, priority=None):
        # search returns different fields w.r.t. edges compared to `get` api,
        # different method to keep `self.get` clean.
        item = self.item_from_json(item_json, add_to_local_db=add_to_local_db, priority=priority)
        item.reset_local_sync_state()

        for edge_json in item_json.get("[[edges]]", []):
            edge_name = edge_json["_edge"]
            try:
                edge_item = self.item_from_json(
                    edge_json["_item"],
                    add_to_local_db=add_to_local_db,
                    priority=priority,
                )
                edge_item.reset_local_sync_state()
                item.add_edge(edge_name, edge_item)
            except Exception as e:
                logger.error(f"Could not attach edge {edge_json['_item']} to {item}, {e}")
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
        add_to_local_db: bool = True,
        priority=None,
    ) -> ItemBase:
        priority = Priority(priority) if priority else None

        item_class = get_schema_cls(
            json["type"],
            extra=self.registered_classes,
        )

        new_item = item_class.from_json(json)
        if add_to_local_db:
            new_item = self.add_to_store(new_item, priority=priority)
        if getattr(new_item, "requires_client_ref", False):
            new_item._client = self
        return new_item

    def _item_from_graphql(self, data):
        item = self.item_from_json(data)
        for prop in item.edges:
            if prop in data:
                for edge in data[prop]:
                    edge_item = self._item_from_graphql(edge)
                    item.add_edge(prop, edge_item)
        return item

    def search_graphql(
        self, query: Union[str, GQLQuery], variables: Optional[Dict[str, Any]] = None
    ) -> List[ItemBase]:
        response = self.api.graphql(query, variables)
        data = response["data"]
        result = []
        for d in data:
            item = self._item_from_graphql(d)
            result.append(item)
        return result

    def send_email(self, to, subject="", body=""):
        try:
            self.api.send_email(to, subject, body)
            logger.info(f"succesfully sent email to {to}")
            return True
        except PodError as e:
            logger.error(e)
            return False

    def sync(self, priority: str = Priority.newest):
        priority = Priority(priority) if priority else None
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
                    warnings.warn(
                        f"Could not sync `{edge.name}` for {item}: edge target missing in sync."
                    )

        update_ids = [item.id for item in update_items]
        existing_items = self.search({"ids": update_ids}, add_to_local_db=True, priority=priority)

        return self.bulk_action(
            create_items=create_items,
            update_items=update_items,
            create_edges=create_edges,
            priority=priority,
        )

    def get_dataset(self, name):
        datasets = self.search({"type": "Dataset", "name": name})
        if len(datasets) == 0:
            raise PodError(f"No datasets found with name {name}")
        elif len(datasets) > 1:
            warnings.warn(f"Multiple datasets found with name {name}. Using the newest dataset.")
        return datasets[-1]

    def send_trigger_status(self, item_id, trigger_id, status):
        try:
            self.api.send_trigger_status(item_id, trigger_id, status)
            return True
        except Exception as e:
            logger.error("Failed to send trigger status to the POD")
            return False

    def get_oauth2_access_token(self, platform):
        try:
            return self.api.oauth2get_access_token(platform)["accessToken"]
        except PodError as e:
            logger.error(e)
            return None

    def plugin_status(self, plugins):
        try:
            return self.api.plugin_status(plugins)["plugins"]
        except PodError as e:
            logger.error(e)
            return None

    def get_oauth1_request_token(self, platform, callback_url):
        return self.api.oauth1_request_token(platform, callback_url)

    def get_oauth1_access_token(self, oauth_token, oauth_verifier, oauth_token_secret):
        return self.api.oauth1_access_token(
            oauth_token=oauth_token,
            oauth_verifier=oauth_verifier,
            oauth_token_secret=oauth_token_secret,
        )

    def oauth2_authorize(self, *, platform, code, redirect_uri):
        try:
            return self.api.oauth2authorize(
                code=code, platform=platform, redirect_uri=redirect_uri
            )["accessToken"]
        except PodError as e:
            logger.error(e)
            return None

    def get_oauth2_authorization_url(self, platform, scopes, redirect_uri):
        try:
            return self.api.oauth2get_authorization_url(platform, scopes, redirect_uri)
        except PodError as e:
            logger.error(e)
            return None
