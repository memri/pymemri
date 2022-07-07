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

def send_email(plugin_run, client, full_user_auth_url):
    # To make auth possible without email, attach url to pluginrun.
    plugin_run.authUrl = full_user_auth_url

    # Gather email
    plugin_run.status = RUN_USER_ACTION_NEEDED
    email_cvu = get_default_cvu("request_email.cvu")
    client.bulk_action(
        create_items=[email_cvu],
        create_edges=[Edge(plugin_run, email_cvu, "view")]
    )
    client.update_item(plugin_run)

	# Poll until status == "ready"
    print("Polling for email...")
    while plugin_run.status != RUN_USER_ACTION_COMPLETED:
        sleep(1)
        plugin_run = client.get(plugin_run.id)

    # send email
    print("Sending email...")
    try:
        to = plugin_run.account[0].authEmail
        if to is None:
            raise ValueError("no auth email")
        client.send_email(to, subject="The link to your qr code", body=full_user_auth_url)
        email_sent = True
    except Exception as e:
        email_sent = False
        print(f"failed to send email:\n{e}")

    # depending on whether email was a success, either show qr link, or message that link was sent to email
    if not email_sent:
        # NOTE Theres currently no documented way to delete edges, so client will have to pick the last added cvu.
        client.bulk_action(delete_items=[email_cvu])
        cvu = get_default_cvu("qr_code_auth.cvu")
        client.create(cvu)
        plugin_run.add_edge("view", cvu)
        client.create_edge(plugin_run.get_edges("view")[0])
        plugin_run.status = RUN_USER_ACTION_NEEDED
        plugin_run.authUrl = full_user_auth_url
        client.update_item(plugin_run)

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

    process_email = multiprocessing.Process(target=send_email, args=(plugin_run, client, full_user_auth_url), daemon=True)
    process_email.start()
