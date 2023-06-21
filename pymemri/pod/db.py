from enum import Enum

from loguru import logger

from ..data.schema import Item


class Priority(Enum):
    newest = "newest"
    local = "local"
    remote = "remote"
    error = "error"


class DB:
    def __init__(self):
        self.nodes = dict()

    def add(self, node):
        id = node.id
        if id in self.nodes:
            logger.error(
                f"Error trying to add node, but node with with id: {id} is already in database"
            )
        self.nodes[id] = node

    def get(self, id):
        res = self.nodes.get(id, None)
        return res

    def contains(self, node):
        return node.id in self.nodes

    def merge(self, node, priority):
        if self.contains(node):
            node = self._merge_item(self.get(node.id), node, priority)
        else:
            self.add(node)
        return node

    def _merge_item(self, local_item: Item, remote_item: Item, priority: Priority) -> Item:
        """
        Merge the properties and edges of `remote_item` into `local_item`, according to `priority`

        Possible priorities:
        "newest": In case of a conflict, use the local property
                  if it was modified after remote_item.date_server_modified
        "local": In case of a conflict, use the local property value
        "remote": In case of a conflict, use the remote property value
        "error": throw a `ValueError` on conflict
        """
        if not isinstance(remote_item, type(local_item)):
            logger.warning(
                f"Trying to merge items of different types: {type(local_item)} and {type(remote_item)}"
            )

        for prop in local_item.properties:
            self._merge_property(local_item, remote_item, prop, priority)

        self._merge_edges(local_item, remote_item)
        return local_item

    def _merge_property(self, local_item, remote_item, prop, priority):
        local_val = getattr(local_item, prop)
        remote_val = getattr(remote_item, prop)
        orig_val = local_item._original_properties.get(prop, None)

        if prop == "dateServerModified":
            setattr(local_item, prop, remote_val)
            return

        # Property is not updated locally since last sync, always use remote
        if prop not in local_item._original_properties:
            setattr(local_item, prop, remote_val)

        elif priority == Priority.newest:
            # Note: Pod does not have a DSM per property, so we compare against the Item DSM.
            dateLocalModified = local_item._date_local_modified.get(prop, None)
            if remote_val != orig_val and remote_item.dateServerModified > dateLocalModified:
                setattr(local_item, prop, remote_val)

        elif priority == Priority.remote:
            if orig_val != remote_val:
                setattr(local_item, prop, remote_val)

        elif priority == Priority.local:
            return

        elif priority == Priority.error:
            raise ValueError(f"Sync conflict on `{prop}` property for {local_item}")

        else:
            raise ValueError(f"Unknown sync priority: {priority}")

    def _merge_edges(self, local_item, remote_item):
        for edge in local_item.edges:
            local_edges = local_item.__edges__[edge]
            remote_edges = remote_item.__edges__[edge]
            local_edges.extend([edge for edge in remote_edges if edge not in local_edges])
            for edge in local_edges:
                edge.source = local_item
