from pymemri.pod.client import PodClient


def _add_to_schema_export(*items):
    pass

def export_schema(plugin):
    client = PodClient()
    client.add_to_schema = _add_to_schema_export
