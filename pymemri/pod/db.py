# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/pod.db.ipynb (unless otherwise specified).

__all__ = ['DB']

# Cell
# hide
class DB():
    def __init__(self):
        self.nodes = dict()

    def add(self, node):
        id = node.id
        if id in self.nodes:
            print(f"Error trying to add node, but node with with id: {id} is already in database")
        self.nodes[id] = node

    def get(self, id):
        res = self.nodes.get(id, None)
        return res

    def contains(self, node):
        id = node.get_property("id")
        return id in self.nodes

    def create(self, node):
        existing = self.get(node.properties.get("id", None))

        if existing is not None:
            if not existing._expanded:
                existing.edges = node.edges
                existing._expanded = node.edges is not None
            return existing
        else:
            self.add(node)
            return node