
from time import sleep
from pymemri.webserver.models.trigger import FilterBatch, FilterDaily, RegisterReq, TriggerReq
from .pluginbase import PluginBase
import abc
import threading
from datetime import datetime, timedelta

class TriggerPluginBase(PluginBase):
    """Base class for plugins that are expected to expose HTTP interface used by the POD.
       Current use case is to notify the plugin about arrival of new data."""

    def __init__(self, pluginRun=None, client=None, **kwargs):
        """The pluginRun argument keeps information about port used to setup the web server"""
        super().__init__(pluginRun=pluginRun, client=client, **kwargs)

        self._triggers = dict()

        # Pass a closure to the fastapi route
        self._webserver.app.add_api_route("/v1/item/trigger", self.do_trigger, methods=["POST"])
        self._webserver.app.add_api_route("/v1/trigger/register", self.do_register, methods=["POST"])


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

    def do_register(self, req: RegisterReq):
        """ Registers the trigger """
        print("Got register req ")

        if isinstance(req.filter, FilterDaily):
            print("request contains daily")

            def thread_fn(filter: FilterDaily, trigger_id: str):

                while True:
                    # self.client
                    now = datetime.utcnow()
                    now_td = timedelta(hours=now.hour, minutes=now.minute)

                    alarm = datetime.strptime(filter.time, "%H:%M")
                    alarm_td = timedelta(hours=alarm.hour, minutes=alarm.minute)

                    # Timedelta normalizes seconds attribute to be always in range [0, number of seconds in one day)
                    # here we subtract two time deltas that are less than one day
                    time_to_wait = now_td - alarm_td

                    print(f"time_to_wait {time_to_wait}")
                    sleep(5)

                    result = self.client.get(trigger_id)

                    print(f"result: {result}")

                pass

            handle = threading.Thread(target=thread_fn, args=(req.filter, req.trigger_id), daemon=True)
            handle.start()
            self._triggers[req.trigger_id] = (req.filter, handle)

        elif isinstance(req.filter, FilterBatch):
            print("request contains batch")



    @abc.abstractmethod
    def trigger(self, req: TriggerReq):
        """
        Handler of new data arrival, argument holds required details
        @throws Exception in any error encountered
        """
        raise NotImplementedError()
