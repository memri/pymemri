import inspect
import json
from typing import Dict

from pymemri.data.schema import _central_schema
from pymemri.data.schema._central_schema import Item


def get_central_schema() -> Dict[str, type]:
    # same as pymemri.data.schema.get_schema, but only imports _central_schema classes
    return {
        k: v
        for k, v in inspect.getmembers(_central_schema)
        if inspect.isclass(v) and issubclass(v, Item)
    }


all_schema = []
for schema_type in get_central_schema().values():
    all_schema.extend(schema_type.pod_schema())


with open("schema.json", "w") as f:
    json.dump(all_schema, f, indent=2)
