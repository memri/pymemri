import erdantic as erd

from pymemri.schema import get_schema

schema = get_schema()
models = list(schema.values())
for model in models:
    model.update_forward_refs()

erd.draw(*models, out="diagram.png")
