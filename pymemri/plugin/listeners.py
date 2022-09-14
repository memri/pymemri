import os
import signal
import threading
import time
from http import HTTPStatus
from threading import Thread
from typing import Callable

from pymemri.pod.api import PodError
from pymemri.pod.client import PodClient

from .states import RUN_COMPLETED, RUN_FAILED


class PluginRunStatusListener:
    def __init__(self, client, run_id, status, callback, interval=5, verbose=False):
        self.client = client
        self.run_id = run_id
        self.status = status
        self.callback = callback
        self.interval = interval
        self.verbose = verbose
        self.running = True

    def stop(self):
        if self.verbose:
            print("Stopping listener...", flush=True)
        self.running = False

    def run(self):
        if self.verbose:
            print(f"Listening for status='{self.status}' on Item {self.run_id}", flush=True)

        while self.running and threading.main_thread().is_alive():
            time.sleep(self.interval)
            try:
                run = self.client.get(self.run_id)
                if self.verbose:
                    print("run status:", run.status, flush=True)
                if run.status == self.status:
                    self.callback()
            except Exception as e:
                print(f"Could not get run in status listener: {e}")


class PodHTTPStatusListener:
    def __init__(
        self,
        client: PodClient,
        run_id: str,
        callback: Callable,
        http_status: HTTPStatus,
        interval: int = 5,
        verbose: bool = False,
    ) -> None:
        """calls `self.callback` if the a pod request with pluginauth encounters self.http_status.

        Required for stopping plugins when the pod returns MISDIRECTED_REQUEST; on pod restart,
        pluginauth keys are lost, and the plugin can no longer connect to the Pod.

        Args:
            client (PodClient): the PodClient to check status for.
            run_id (str): the id of the plugin to check the http status for.
            callback (function): Function that is triggered when http_status is encountered.
            http_status (HTTPStatus): HTTPStatus received from pod that triggers callback.
            interval (int, optional): Interval the pod status is checked. Defaults to 60.
            verbose (bool, optional): Listener prints additional information if True. Defaults to False.
        """
        self.client: PodClient = client
        self.run_id = run_id
        self.callback = callback
        self.interval = interval
        self.verbose = verbose
        self.http_status = http_status
        self.running = True

    def stop(self):
        if self.verbose:
            print("Stopping listener...", flush=True)
        self.running = False

    def run(self):
        if self.verbose:
            print(f"Listening for pod http status {self.http_status.value}", flush=True)

        while self.running and threading.main_thread().is_alive():
            time.sleep(self.interval)
            try:
                _ = self.client.api.get_item(self.run_id)
                if self.verbose:
                    print("run http status OK", flush=True)
            except PodError as e:
                if self.verbose:
                    print("run http status:", e.status, flush=True)
                if e.status == self.http_status:
                    self.callback()
            except Exception as e:
                print(f"Could not get run in httpstatus listener: {e}")


def force_exit_callback():
    print("Listener aborted plugin...", flush=True)
    pid = os.getpid()
    os.kill(pid, signal.SIGINT)


def get_abort_plugin_listener(client, run_id, **kwargs):
    listener = PluginRunStatusListener(
        client=client, run_id=run_id, status="aborted", callback=force_exit_callback, **kwargs
    )
    thread = Thread(
        target=listener.run,
    )
    thread.start()
    return listener


def get_pod_restart_listener(client, run_id, **kwargs):
    listener = PodHTTPStatusListener(
        client=client,
        run_id=run_id,
        callback=force_exit_callback,
        http_status=HTTPStatus.MISDIRECTED_REQUEST,
        interval=60,
        **kwargs,
    )
    thread = Thread(target=listener.run)
    thread.start()
    return listener
