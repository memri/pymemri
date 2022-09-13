import threading
import time

import pytest

from pymemri.data.schema import Account, PluginRun
from pymemri.plugin.authenticators.password import (
    PasswordAuthenticator,
    set_account_credentials,
)
from pymemri.plugin.pluginbase import PluginBase
from pymemri.pod.client import PodClient


@pytest.fixture
def client():
    return PodClient()


class MyAuthenticatedPlugin(PluginBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logged_in = False
        self.authenticator = PasswordAuthenticator(self.client, self.pluginRun)

    def login(self, username, password):
        if not (username == "username" and password == "password"):
            raise ValueError("Wrong credentials.")

    def run(self):
        self.authenticator.authenticate(login_callback=self.login)
        self.logged_in = True
        print("done!")


def test_password_plugin(client):
    # Create Plugin
    run = PluginRun("", "", "")
    account = Account(service="myAccount")
    run.add_edge("account", account)
    client.create(run)
    client.create(account)
    client.create_edge(run.get_edges("account")[0])

    plugin = MyAuthenticatedPlugin(client=client, pluginRun=run)
    thread = threading.Thread(target=plugin.run, daemon=True)
    thread.start()

    # Enter password and check if plugin is authenticated
    time.sleep(0.5)
    set_account_credentials(client, run.id, "username", "password")
    time.sleep(0.5)
    thread.join()
    assert plugin.logged_in
