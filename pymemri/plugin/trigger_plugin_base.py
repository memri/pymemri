
from pymemri.webserver.models.trigger import TriggerReq
from .pluginbase import PluginBase
import abc
import threading


class TriggerPluginBase(PluginBase):
    """Base class for plugins that are expected to expose HTTP interface used by the POD.
       Current use case is to notify the plugin about arrival of new data."""

    def __init__(self, pluginRun=None, client=None, **kwargs):
        """The pluginRun argument keeps information about port used to setup the web server"""
        super().__init__(pluginRun=pluginRun, client=client, **kwargs)

        # Pass a closure to the fastapi route
        self._webserver.app.add_api_route("/v1/item/trigger", self.do_trigger, methods=["POST"])

    def do_trigger(self, req: TriggerReq):
        """ Handle trigger request for given item. Item must be present already in the POD.
            Operation is offloaded to a dedicated thread, the POD is notified about the status
            asynchronously."""
        def thread_fn(req: TriggerReq):
            try:
                self.trigger(req)
                self.client.send_trigger_status(req.item_id, req.trigger_id, "OK")

            except Exception as e:
                msg = f"Error while handling the trigger for item {req}, reason {e}"
                print(msg)
                self.client.send_trigger_status(req.item_id, req.trigger_id, msg)

        threading.Thread(target=thread_fn, args=(req,)).start()

        return "ok"

    @abc.abstractmethod
    def trigger(self, req: TriggerReq):
        """
        Handler of new data arrival, argument holds required details
        @throws Exception in any error encountered
        """
        raise NotImplementedError()
