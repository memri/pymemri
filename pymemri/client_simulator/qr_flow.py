import requests
from pymemri.data.itembase import Edge
from pymemri.plugin.schema import  PluginRun
from pymemri.pod.client import PodClient
import multiprocessing
from time import sleep
import os
from pymemri.plugin.states import RUN_USER_ACTION_NEEDED, RUN_USER_ACTION_COMPLETED
from pymemri.plugin.pluginbase import POD_PLUGIN_DNS_ENV
from pymemri.cvu.utils import get_default_cvu


def run_qr_flow(client: PodClient, plugin_run: PluginRun):
    host = "0.0.0.0"
    port = plugin_run.webserverPort or 8080
    # give time to start
    print("Checking if webservice is ready...")
    ready = False
    while not ready:
        try:
            ready = requests.get(f"http://{host}:{port}/qr").status_code in [200, 201]
        except Exception as e:
            print(f"The QR server is not ready yet: '{e}'")

        sleep(0.2)

    user_host = os.environ.get(POD_PLUGIN_DNS_ENV, f"http://0.0.0.0:{port}")
    full_user_auth_url = f"{user_host}/qr"

    print(f"GO TO {full_user_auth_url} and scan the code")
