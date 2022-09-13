from pymemri.plugin.pluginbase import PluginBase
from pymemri.data.schema import Message


class ExamplePlugin(PluginBase):
    schema_classes = [Message]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        print("Started plugin run...")
        message = Message(content="test")
        self.client.create(message)
        print("Run success!")
