from pymemri.data.itembase import Edge
from pymemri.plugin.schema import Account, PluginRun
from pymemri.pod.client import PodClient
import flask
import multiprocessing
from flask import render_template
from time import sleep
import os
from pymemri.plugin.states import RUN_USER_ACTION_NEEDED, RUN_USER_ACTION_COMPLETED
from pymemri.plugin.pluginbase import POD_PLUGIN_DNS_ENV, PluginBase
from pymemri.cvu.utils import get_default_cvu

app = flask.Flask(__name__, template_folder='template')
qr_code_dict = None

QR_CODE_KEY = "qr_code"


@app.route('/qr')
def index():
    global qr_code_dict
    qr_code_data = qr_code_dict[QR_CODE_KEY]
    done = qr_code_dict.get("authenticated", False)
    if done:
        return render_template("success.html")
    else:
        return render_template('images.html', chart_output=qr_code_data)

def run_app(qr_dict, host="0.0.0.0", port=8080):
    global qr_code_dict
    qr_code_dict = qr_dict
    app.run(host=host, port=port)

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

def run_qr_flow(_qr_code_data, client: PodClient, plugin_run: PluginRun):
    manager = multiprocessing.Manager()
    process_dict = manager.dict()
    process_dict["qr_code"] = _qr_code_data
    process_dict["authenticated"] = False
    host = "0.0.0.0"
    port = 8080
    user_host = os.environ.get(POD_PLUGIN_DNS_ENV, f"http://0.0.0.0:{port}")
    full_user_auth_url = f"{user_host}/qr"
    process = multiprocessing.Process(target=run_app, args=(process_dict,),
                                      kwargs={"host": host, "port": port}, daemon=True)
    process.start()

    print(f"GO TO {full_user_auth_url} and scan the code")

    process_email = multiprocessing.Process(target=send_email, args=(plugin_run, client, full_user_auth_url), daemon=True)
    process_email.start()
    
    return process, process_dict

if __name__ == "__main__":
    # this is here for testing purposes, no function in production
    qr_code_data ="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGhlaWdodD0iMjcwIiB3aWR0aD0iMjcwIiBjbGFzcz0icHlxcmNvZGUiPjxwYXRoIGZpbGw9InJnYmEoMCwwLDAsMC4wKSIgZD0iTTAgMGgyNzB2MjcwaC0yNzB6Ii8+PHBhdGggdHJhbnNmb3JtPSJzY2FsZSg2KSIgc3Ryb2tlPSIjMTIyRTMxIiBjbGFzcz0icHlxcmxpbmUiIGQ9Ik0wIDAuNWg3bTUgMGgybTMgMGgxbTQgMGgybTEgMGgxbTIgMGg1bTMgMGgxbTEgMGg3bS00NSAxaDFtNSAwaDFtMSAwaDFtMyAwaDNtMSAwaDFtMSAwaDJtNCAwaDFtNyAwaDJtMSAwaDFtMiAwaDFtNSAwaDFtLTQ1IDFoMW0xIDBoM20xIDBoMW0yIDBoMm0yIDBoMm00IDBoMW0xIDBoMW0xIDBoMW0xIDBoMW0yIDBoMW0xIDBoMm0xIDBoMW0xIDBoMW0yIDBoMW0xIDBoM20xIDBoMW0tNDUgMWgxbTEgMGgzbTEgMGgxbTEgMGgxbTQgMGgxbTEgMGgxbTEgMGgzbTEgMGgybTEgMGgxbTUgMGgybTMgMGgybTEgMGgxbTEgMGgzbTEgMGgxbS00NSAxaDFtMSAwaDNtMSAwaDFtMiAwaDRtMSAwaDFtMyAwaDhtMSAwaDJtMSAwaDNtMSAwaDNtMSAwaDFtMSAwaDNtMSAwaDFtLTQ1IDFoMW01IDBoMW0xIDBoMW0xIDBoMW0zIDBoM20zIDBoMW0zIDBoMW0xIDBoNG04IDBoMW01IDBoMW0tNDUgMWg3bTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGg3bS0zMyAxaDJtMSAwaDFtMSAwaDJtMSAwaDFtMyAwaDJtMSAwaDFtMSAwaDJtMSAwaDVtLTM3IDFoNW0xIDBoM20xIDBoNG0xIDBoMm0xIDBoMW0xIDBoNm0zIDBoMW0xIDBoMW0yIDBoMW0yIDBoMW0xIDBoMW0xIDBoMW0xIDBoMW0tNDMgMWgxbTIgMGgxbTIgMGgxbTEgMGgzbTEgMGgybTIgMGgxbTEgMGgxbTMgMGgxbTQgMGgzbTUgMGgxbTQgMGgxbTIgMGgxbS00NSAxaDNtMSAwaDRtNSAwaDFtMyAwaDRtMyAwaDVtMSAwaDJtMSAwaDFtMSAwaDVtMSAwaDJtLTM5IDFoMW0zIDBoNW0xIDBoMW0xIDBoMW0xIDBoMm0xIDBoMW0xIDBoMW0xIDBoM20yIDBoM20yIDBoMW0xIDBoMW0xIDBoMW0yIDBoMW0tNDMgMWgybTIgMGgxbTEgMGgxbTUgMGgybTEgMGgxbTEgMGg0bTEgMGgybTYgMGgxbTIgMGg1bTMgMGgxbTIgMGgxbS00NCAxaDFtMSAwaDFtMyAwaDFtMSAwaDNtMSAwaDFtNCAwaDFtMyAwaDFtMSAwaDJtNCAwaDJtMyAwaDNtMyAwaDFtMSAwaDJtLTQ0IDFoMW00IDBoM20yIDBoMW0xIDBoMW0xIDBoMW0xIDBoMm0xIDBoMm0xIDBoMm0yIDBoMm01IDBoMm0xIDBoMm0xIDBoMm0tNDIgMWgxbTEgMGgxbTEgMGgxbTIgMGg0bTEgMGgzbTQgMGgxbTEgMGgxbTEgMGgybTIgMGgybTEgMGgzbTIgMGgybTIgMGgxbTEgMGg0bS00NSAxaDFtMiAwaDRtMSAwaDFtMSAwaDRtMSAwaDVtMSAwaDNtMSAwaDNtMSAwaDFtNCAwaDFtNyAwaDJtLTQ0IDFoNG0xIDBoMW0xIDBoMW0xIDBoMW0xIDBoMW0xIDBoMW00IDBoNG0zIDBoMW0yIDBoNG0zIDBoM20xIDBoMW0xIDBoMW0tNDIgMWgybTEgMGgxbTEgMGgzbTQgMGgxbTEgMGgxbTEgMGgybTEgMGgxbTEgMGg0bTQgMGgxbTMgMGgxbTIgMGgybTIgMGg0bS00NCAxaDJtMSAwaDFtMSAwaDFtMSAwaDFtMSAwaDJtMSAwaDFtMyAwaDFtMSAwaDJtNCAwaDFtMSAwaDNtMiAwaDJtMyAwaDFtMiAwaDFtMiAwaDFtLTM5IDFoN20xIDBoMm0xIDBoMW0xIDBoMm0xIDBoN20yIDBoMW00IDBoN20tNDAgMWgybTEgMGgxbTMgMGgybTMgMGgybTIgMGgybTEgMGgxbTMgMGgybTEgMGgxbTEgMGg0bTIgMGgybTMgMGgxbTIgMGgybS00NCAxaDRtMSAwaDFtMSAwaDJtMSAwaDNtMyAwaDFtMSAwaDJtMSAwaDFtMSAwaDJtMyAwaDFtMSAwaDNtMSAwaDJtMSAwaDFtMSAwaDRtLTQwIDFoMW0zIDBoM200IDBoNm0zIDBoMW0xIDBoMW0xIDBoMW0xIDBoM20xIDBoMW0xIDBoMW0zIDBoNG0tNDAgMWgxMG0xIDBoNG0xIDBoNW0yIDBoMW0zIDBoMW0zIDBoNm0tNDEgMWgxbTIgMGgxbTEgMGgxbTEgMGg0bTEgMGgybTEgMGgxbTQgMGgybTMgMGgxbTEgMGg0bTUgMGgxbTQgMGgxbS00MSAxaDFtMiAwaDRtMyAwaDNtNCAwaDFtMiAwaDJtMSAwaDRtMSAwaDFtMSAwaDJtMSAwaDFtMiAwaDFtMiAwaDFtMSAwaDJtLTQzIDFoMm0xIDBoMW0zIDBoMm0yIDBoMW0zIDBoNG0yIDBoM20zIDBoM20yIDBoMW0zIDBoMW0xIDBoMW0xIDBoM20tNDAgMWg0bTIgMGgybTEgMGgxbTIgMGgzbTYgMGgybTIgMGgxbTEgMGgxbTcgMGgybTEgMGgxbS00MyAxaDFtMiAwaDJtMyAwaDNtMSAwaDFtNCAwaDRtMiAwaDNtMSAwaDRtMSAwaDFtNSAwaDFtNCAwaDJtLTQ1IDFoMW0xIDBoMW0xIDBoMW0xIDBoNm00IDBoMW0zIDBoMm00IDBoMW00IDBoMW0xIDBoMm0yIDBoMW0yIDBoMW0tNDEgMWg1bTUgMGg0bTEgMGgxbTEgMGgxbTUgMGgzbTMgMGgybTIgMGgxbTEgMGgxbTIgMGgybTIgMGgybS00MyAxaDFtMyAwaDNtMiAwaDFtMSAwaDFtMiAwaDFtMSAwaDNtNSAwaDJtMiAwaDNtMiAwaDFtMSAwaDFtMSAwaDFtMSAwaDFtMiAwaDJtLTQ0IDFoMW0xIDBoMW02IDBoMm0xIDBoMm0zIDBoM20xIDBoMW0xIDBoMm0xIDBoNW0zIDBoMm0yIDBoMW0zIDBoMm0tNDEgMWgxbTEgMGgybTEgMGgxbTMgMGgxbTEgMGgxbTQgMGg0bTEgMGg2bTEgMGgxbTQgMGgxbTEgMGgybS00MCAxaDRtMiAwaDJtMiAwaDFtMSAwaDFtMSAwaDJtMSAwaDRtMiAwaDJtMiAwaDFtMiAwaDJtMiAwaDhtLTQzIDFoMW0yIDBoMm0xIDBoMm0yIDBoMm01IDBoMm0xIDBoNW00IDBoMm0yIDBoMm0xIDBoNW0xIDBoMW0xIDBoMW0tMzcgMWgxbTEgMGgxbTEgMGgzbTUgMGgxbTMgMGgybTEgMGgybTEgMGgxbTUgMGgxbTMgMGgxbTMgMGgxbS00NSAxaDdtMSAwaDJtMSAwaDFtMSAwaDNtMyAwaDJtMSAwaDFtMSAwaDFtMiAwaDFtMyAwaDFtMiAwaDNtMSAwaDFtMSAwaDJtMSAwaDFtLTQ0IDFoMW01IDBoMW0yIDBoMm0xIDBoMm0xIDBoNm0zIDBoMm0yIDBoNG0xIDBoMW0xIDBoMm0zIDBoM20xIDBoMW0tNDUgMWgxbTEgMGgzbTEgMGgxbTEgMGgxbTEgMGgxbTEgMGgxbTIgMGgxbTEgMGgybTEgMGg1bTYgMGgxbTIgMGgxbTEgMGg2bTEgMGgxbS00NCAxaDFtMSAwaDNtMSAwaDFtMSAwaDJtMiAwaDNtMyAwaDFtNiAwaDFtMiAwaDFtMSAwaDJtMyAwaDFtMSAwaDFtMSAwaDVtLTQ0IDFoMW0xIDBoM20xIDBoMW0xIDBoNm01IDBoMW0zIDBoNW0xIDBoMW0xIDBoMW00IDBoMW0xIDBoMW0yIDBoMm0xIDBoMW0tNDUgMWgxbTUgMGgxbTEgMGgybTEgMGgxbTEgMGgxbTEgMGgxbTMgMGgybTIgMGgxbTEgMGgybTEgMGgxbTMgMGg2bTEgMGgxbTEgMGgybS00MyAxaDdtMSAwaDNtMiAwaDFtMiAwaDFtMSAwaDJtMiAwaDZtMSAwaDFtMSAwaDFtMSAwaDFtMiAwaDFtMiAwaDJtMiAwaDEiLz48L3N2Zz4K"
    process = run_qr_flow(qr_code_data)
    i=0
    while i<3:
        i+=1
        sleep(1)
        print("waiting")
    