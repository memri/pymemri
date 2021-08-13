from pymemri.pod.client import PodClient
import time
from fastscript import call_parse, Param

SLEEP_INTERVAL = 1

def input_credentials():
    username = input("Enter username: ")
    password = input("Enter password: ")
    return username, password

@call_parse
def run_password_simulator(
    database_key: Param("database key", str)=None,
    owner_key: Param("owner key", str)=None,
    run_id: Param("owner key", str)=None
):

    client = PodClient(database_key=database_key, owner_key=owner_key)

    while True:
        time.sleep(SLEEP_INTERVAL)
        pluginRun = client.get(run_id)
        account = pluginRun.account[0]

        if pluginRun.status == "userActionNeeded":
            username, password = input_credentials()
            print(username, password)
            account.identifier = username
            account.secret = password
            pluginRun.status = "ready"
            client.update_item(pluginRun)
            client.update_item(account)
            print("Done authenticating")
            break

        elif pluginRun.status == "started":
            print("plugin starting...")

        elif pluginRun.status == "ready":
            print("no user action needed.")

        elif pluginRun.status == "error":
            print("error occurred in plugin.")
            break
    
        elif pluginRun.status == "done":
            break

        else:
            print(f"unknown plugin state {pluginRun.status}.")