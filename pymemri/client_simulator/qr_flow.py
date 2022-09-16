import os
from time import sleep

import requests
from loguru import logger

from pymemri.data.schema import PluginRun
from pymemri.plugin.constants import POD_PLUGIN_DNS_ENV
from pymemri.pod.client import PodClient


def run_qr_flow(client: PodClient, plugin_run: PluginRun):
    host = "0.0.0.0"
    port = plugin_run.webserverPort or 8080
    # give time to start
    logger.info("Checking if webservice is ready...")
    ready = False
    while not ready:
        try:
            ready = requests.get(f"http://{host}:{port}/qr").status_code in [200, 201]
        except Exception as e:
            logger.info(f"The QR server is not ready yet: '{e}'")

        sleep(0.2)

    user_host = os.environ.get(POD_PLUGIN_DNS_ENV, f"http://0.0.0.0:{port}")
    full_user_auth_url = f"{user_host}/qr"

    logger.info(f"GO TO {full_user_auth_url} and scan the code")
