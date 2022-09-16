import time

from fastscript import Param, call_parse
from loguru import logger

from pymemri.plugin.states import (
    RUN_COMPLETED,
    RUN_FAILED,
    RUN_STARTED,
    RUN_USER_ACTION_COMPLETED,
    RUN_USER_ACTION_NEEDED,
)
from pymemri.pod.client import PodClient

SLEEP_INTERVAL = 1


def input_credentials():
    username = input("Enter username: ")
    password = input("Enter password: ")
    return username, password


@call_parse
def run_password_simulator(
    database_key: Param("database key", str) = None,
    owner_key: Param("owner key", str) = None,
    run_id: Param("owner key", str) = None,
):

    print("FRONTEND PASSWORD SIMULATOR")
    if database_key and owner_key:
        logger.info("pod credentials from from args")
        client = PodClient(database_key=database_key, owner_key=owner_key)
    else:
        client = PodClient.from_local_keys()

    while True:
        time.sleep(SLEEP_INTERVAL)
        pluginRun = client.get(run_id)
        account = pluginRun.account[0]

        if pluginRun.status == RUN_USER_ACTION_NEEDED:
            username, password = input_credentials()
            account.identifier = username
            account.secret = password
            pluginRun.status = "ready"
            client.update_item(pluginRun)
            client.update_item(account)
            logger.info("Done authenticating")
            break

        elif pluginRun.status == RUN_STARTED:
            logger.info("plugin starting...")

        elif pluginRun.status == RUN_USER_ACTION_COMPLETED:
            logger.info("no user action needed.")

        elif pluginRun.status == RUN_FAILED:
            logger.error("error occurred in plugin.")
            break

        elif pluginRun.status == RUN_COMPLETED:
            break

        else:
            logger.warning(f"unknown plugin state {pluginRun.status}.")
