import zipfile
import requests
import io
from pathlib import Path
import json
from jinja2 import Template
import black
import shutil

SCHEMA_URL = "https://gitlab.memri.io/memri/schema/-/archive/dev/schema-dev.zip"
DOWNLOAD_PATH = Path(__file__).parent / "tmp"
BASE_DIR = DOWNLOAD_PATH / "schema-dev" / "TypeHierarchy" / "Item"
OUTPUT_FILE = Path(__file__).parent.parent / "pymemri" / "data" / "central_schema.py"
EXCLUDED_SCHEMAS = {"Item", "Type"}
SCHEMA_TYPES = {
    "Bool": bool,
    "Text": str,
    "Integer": int,
    "Real": float
}

HEADER = """# AUTOGENERATED, DO NOT EDIT!
# This file was generated by /tools/generate_base_schema.py
# Visit https://gitlab.memri.io/memri/schema to learn more 

from .itembase import Item
from typing import Optional
"""

TEMPLATE = '''class {{name}}({{base_schema}}):
    description = """{{description}}"""
    {% if properties is defined %}
    properties = {{base_schema}}.properties + {{properties|map(attribute="name")|list}}{% endif %}    
    {% if edges is defined %}
    edges = {{base_schema}}.edges + {{edges|map(attribute="name")|list}}{% endif %}
    
    
    def __init__(
        self,
        {% for property in properties %}
        {{property.name}}: {{property.type}} = None,
        {% endfor %}
        {% for edge in edges %}
        {{edge.name}}: list = None,
        {% endfor %}
        **kwargs
    ):
        super().__init__(**kwargs)

        {% if properties is defined %}
        # Properties
        {% for property in properties %}
        self.{{property.name}}: Optional[{{property.type}}] = {{property.name}} 
        {% endfor %}{% endif %}

        {% if edges is defined %}
        # Edges
        {% for edge in edges %}
        self.{{edge.name}}: list = {{edge.name}} if {{edge.name}} is not None else []
        {% endfor %}{% endif %}
'''


def generate_from_json(path: Path, schema_template):
    name = path.stem
    base_name = path.resolve().parts[-3]

    with open(path, "r") as f:
        item_dict = json.load(f)

    for item in item_dict["properties"]:
        if item["type"] in SCHEMA_TYPES:
            item["type"] = SCHEMA_TYPES[item["type"]].__name__
        else:
            print(f"skipping unsupported property type {item['type']} in {name}")

    py_str = schema_template.render(
        name=name,
        base_schema=base_name,
        properties=item_dict["properties"],
        edges=item_dict["edges"],
        description=item_dict["description"]
    )
    return py_str


if __name__=="__main__":
    # r = requests.get(SCHEMA_URL)
    # zip = zipfile.ZipFile(io.BytesIO(r.content))
    # zip.extractall(DOWNLOAD_PATH)

    schema_template = Template(TEMPLATE, lstrip_blocks=True, trim_blocks=True)

    generated_schema = []
    for path in BASE_DIR.rglob("*.json"):
        if path.stem in EXCLUDED_SCHEMAS:
            continue
        generated_schema.append(generate_from_json(path, schema_template))

    file_content = "\n\n".join(generated_schema)
    file_content = HEADER + "\n\n" + file_content
    file_content = black.format_str(file_content, mode=black.FileMode())

    with open(OUTPUT_FILE, 'w') as f:
        f.write(file_content)

    # shutil.rmtree(DOWNLOAD_PATH)
