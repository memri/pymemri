# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.listeners.ipynb (unless otherwise specified).

__all__ = ['StatusListener', 'DeleteListener', 'force_exit_callback', 'get_abort_plugin_listener',
           'get_delete_plugin_listener']

# Cell

import time
import os
import signal
import threading
from threading import Thread
from .states import RUN_COMPLETED, RUN_FAILED

# Cell

class StatusListener:
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

# Cell
class DeleteListener:
    def __init__(self, client, run_id, callback, interval=5, verbose=False):
        self.client = client
        self.run_id = run_id
        self.callback = callback
        self.interval = interval
        self.verbose = verbose
        self.running = True

    def stop(self):
        if self.verbose:
            print("Stopping DeleteListener...", flush=True)
        self.running = False

    def run(self):
        if self.verbose:
            print(f"Listening for Plugin Delete on Item {self.run_id}", flush=True)

        while self.running and threading.main_thread().is_alive():
            time.sleep(self.interval)
            try:
                run = self.client.get(self.run_id)
                if self.verbose:
                    print(f"run {self.run_id} deleted {run.deleted}:", flush=True)
                if run.deleted == True:
                    self.callback()
            except Exception as e:
                print(f"Could not get delete state in listener: {e} for {self.run_id}")


# Cell
def force_exit_callback():
    print("Status aborted, killing plugin...", flush=True)
    pid = os.getpid()
    os.kill(pid, signal.SIGINT)

def get_abort_plugin_listener(client, run_id, **kwargs):
    listener = StatusListener(
        client=client,
        run_id=run_id,
        status="aborted",
        callback=force_exit_callback,
        **kwargs
    )
    thread = Thread(
        target=listener.run,
    )
    thread.start()

    return listener

def get_delete_plugin_listener(client, run_id, **kwargs):
    listener = DeleteListener(
        client=client,
        run_id=run_id,
        callback=force_exit_callback,
        verbose=True,
        **kwargs
    )
    thread = Thread(
        target=listener.run,
    )
    thread.start()

    return listener