from glob import glob
import json
from time import sleep
from .pluginbase import PluginBase
import abc
import threading
from flask import Flask, request
from pymemri.pod.client import PodClient

app = Flask(__name__)
TRIGGER_HANDLER = "trigger_handler"


@app.route("/v1/item/trigger", methods=["POST"])
def trigger():
    """Endpoint used to post a request to the plugin that new data arrived. The body of the request
       is a json containing item details"""

    app.config[TRIGGER_HANDLER].do_trigger(request.json)

    return "ok"


class TriggerPluginBase(PluginBase):
    """Base class for plugins that are expected to expose HTTP interface used by the POD.
       Current use case is to notify the plugin about arrival of new data."""

    def __init__(self, pluginRun=None, client=None, **kwargs):
        """The pluginRun argument keeps information about port used to setup the web server"""
        super().__init__(pluginRun=pluginRun, client=client, **kwargs)

        app.config[TRIGGER_HANDLER] = self

        port = pluginRun.webserverPort or 5050

        self._app_handle = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port))
        self._app_handle.start()

    def do_trigger(self, json_arg):
        """ Offload a probably blocking, and time consuming task on a thread,
            collect the result, and notify the POD"""
        def thread_fn(json_arg):
            try:
                self.trigger(**json_arg)
                self.client.send_trigger_status(json_arg["item_id"], json_arg["trigger_id"], "OK")

            except Exception as e:
                msg = f"Error while handling the trigger for item {json_arg}, reason {e}"
                print(msg)
                self.client.send_trigger_status(json_arg["item_id"], json_arg["trigger_id"], msg)

        threading.Thread(target=thread_fn, args=(json_arg,)).start()

    @abc.abstractmethod
    def trigger(self, item_id, trigger_id, **kwargs):
        """
        Handler of new data arrival, argument holds required details
        @throws Exception in any error encountered
        """
        raise NotImplementedError()
