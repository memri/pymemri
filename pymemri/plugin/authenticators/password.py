import getpass
import time
from time import sleep

from fastscript import Param, call_parse
from loguru import logger

from ...cvu.utils import get_default_cvu
from ...pod.client import DEFAULT_POD_ADDRESS, PodClient
from ...pod.utils import read_pod_key
from ..states import RUN_USER_ACTION_COMPLETED, RUN_USER_ACTION_NEEDED
from .credentials import PLUGIN_DIR, read_json, read_username_password


class PasswordAuthenticator:
    DEFAULT_CVU = "password_auth.cvu"
    MAX_LOGIN_ATTEMPTS = 3
    SLEEP_INTERVAL = 1.0
    MAX_POLL_TIME = 600

    def __init__(self, client, pluginRun):
        self.client = client
        self.pluginRun = pluginRun
        self.isTest = False

    def authenticate(self, login_callback):
        self.request_user_credentials()

        login_success = False
        for i in range(self.MAX_LOGIN_ATTEMPTS):
            username, password = self.poll_credentials()
            try:
                login_callback(username, password)
                login_success = True
                break
            except Exception as e:
                logger.error("Login failed, invalid credentials.")
                if self.pluginRun.account:
                    attempts_remaining = self.MAX_LOGIN_ATTEMPTS - (i + 1)
                    account = self.pluginRun.account[0]
                    account.errorMessage = (
                        f"Reached max login attempts. {attempts_remaining} attempts remaining"
                    )
                    self.client.update_item(account)

        if not login_success:
            self.pluginRun.status = "error"
            self.client.update_item(self.pluginRun)

            if self.pluginRun.account:
                account = self.pluginRun.account[0]
                account.errorMessage = "Reached max login attempts."
                self.client.update_item(account)

            raise RuntimeError("Reached max login attempts.")

    def request_user_credentials(self):
        cvu = get_default_cvu(self.DEFAULT_CVU)
        self.client.create(cvu)
        self.pluginRun.add_edge("view", cvu)
        self.client.create_edge(self.pluginRun.get_edges("view")[0])
        self.pluginRun.status = RUN_USER_ACTION_NEEDED
        self.client.update_item(self.pluginRun)

    def poll_credentials(self):
        start_time = time.time()
        while True:
            if time.time() - start_time > self.MAX_POLL_TIME:
                self.pluginRun.status = "error"
                self.client.update_item(self.pluginRun)
                raise RuntimeError("Stop polling, max time reached.")

            sleep(self.SLEEP_INTERVAL)
            self.pluginRun = self.client.get(self.pluginRun.id)
            logger.info(
                f"polling for credentials from account of pluginRun {self.pluginRun.id} ... run.status={self.pluginRun.status}",
            )
            if self.pluginRun.status == RUN_USER_ACTION_COMPLETED:
                account = self.pluginRun.account[0]
                return account.identifier, account.secret


def set_account_credentials(pod_client, run_id, username, password):
    run = pod_client.get(run_id)
    account = run.account[0]
    account.identifier = username
    account.secret = password
    run.status = "ready"

    pod_client.update_item(account)
    pod_client.update_item(run)
    print(f"Setting username and password for {run_id}'s Account'")


@call_parse
def simulate_enter_credentials(
    run_id: Param("run id that requires the password", str) = None,
    plugin: Param("plugin name, used for finding credentials", str) = None,
    pod_full_address: Param("The pod full address", str) = DEFAULT_POD_ADDRESS,
    database_key: Param("Database key of the pod", str) = None,
    owner_key: Param("Owner key of the pod", str) = None,
):
    if database_key is None:
        database_key = read_pod_key("database_key")
    if owner_key is None:
        owner_key = read_pod_key("owner_key")
    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key)
    if plugin is not None:
        try:
            username, password = read_username_password(plugin)
        except Exception as e:
            logger.error(
                f"Could not find credentials for plugin {plugin}, if you don't want to set those locally remove the --plugin arg. Exiting"
            )

            exit()
    else:
        username = input(f"Enter username for service used by {run_id}: ")
        password = getpass.getpass(f"Enter password for service used by {run_id}: ")

    if run_id is None:
        try:
            run_path = PLUGIN_DIR / plugin / "current_run.json"
            logger.info(f"Reading run id from {run_path}")
            run_id = read_json(run_path)["id"]
        except Exception as e:
            logger.error("No run_id specified and could not read current run information")
    set_account_credentials(client, run_id, username, password)
