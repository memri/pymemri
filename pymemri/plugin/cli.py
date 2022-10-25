import json
import os
import time
import traceback
from pathlib import Path

from fastcore.script import Param, call_parse
from loguru import logger

from pymemri import __version__ as pymemri_version

from ..data.basic import write_json
from ..data.schema import PluginRun
from ..pod.client import DEFAULT_POD_ADDRESS, DEFAULT_POD_KEY_PATH, PodClient
from ..pod.utils import DEFAULT_POD_KEY_PATH, POD_KEYS_FULL_FOLDER, read_pod_key
from .constants import (
    POD_AUTH_JSON_ENV,
    POD_FULL_ADDRESS_ENV,
    POD_OWNER_KEY_ENV,
    POD_PLUGIN_DNS_ENV,
    POD_TARGET_ITEM_ENV,
)
from .oauth_handler import run_twitter_oauth_flow
from .pluginbase import (
    PluginError,
    create_run_expanded,
    parse_config,
    parse_metadata,
    run_plugin_from_run_id,
    write_run_info,
)
from .states import RUN_FAILED

logger.info(f"Pymemri version: {pymemri_version}")


def _parse_env():
    env = os.environ
    logger.info("Reading `run_plugin()` parameters from environment variables")
    try:
        pod_full_address = env.get(POD_FULL_ADDRESS_ENV, DEFAULT_POD_ADDRESS)
        plugin_run_json = json.loads(str(env[POD_TARGET_ITEM_ENV]))
        logger.debug(plugin_run_json)
        plugin_run_id = plugin_run_json["id"]
        owner_key = env.get(POD_OWNER_KEY_ENV)
        pod_auth_json = json.loads(str(env.get(POD_AUTH_JSON_ENV)))
        return pod_full_address, plugin_run_id, pod_auth_json, owner_key
    except KeyError as e:
        raise Exception("Missing parameter: {}".format(e)) from None


@call_parse
def store_keys(
    path: Param("path to store the keys", str) = DEFAULT_POD_KEY_PATH,
    database_key: Param("Database key of the pod", str) = None,
    owner_key: Param("Owner key of the pod", str) = None,
    replace: Param("Replace existing stored keys", str) = True,
):

    if not replace:
        try:
            read_pod_key("database_key")
            read_pod_key("owner_key")
            logger.info("Existing stored keys found, exiting without generating new keys.")
            return
        except ValueError:
            pass

    if database_key is None:
        database_key = PodClient.generate_random_key()
    if owner_key is None:
        owner_key = PodClient.generate_random_key()

    obj = {"database_key": database_key, "owner_key": owner_key}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        timestr = time.strftime("%Y%m%d-%H%M%S")
        path.rename(POD_KEYS_FULL_FOLDER / f"keys-{timestr}.json")
    write_json(obj, path)


@call_parse
def run_plugin(
    pod_full_address: Param("The pod full address", str) = DEFAULT_POD_ADDRESS,
    plugin_run_id: Param("Run id of the plugin to be executed", str) = None,
    database_key: Param("Database key of the pod", str) = None,
    owner_key: Param("Owner key of the pod", str) = None,
    read_args_from_env: Param("Read the args from the environment", bool) = False,
    metadata: Param("metadata file for the PluginRun", str) = None,
    config_file: Param(
        "A plugin configuration, overwrites the configuration of the PluginRun", str
    ) = None,
):

    if read_args_from_env:
        pod_full_address, plugin_run_id, pod_auth_json, owner_key = _parse_env()
        database_key = None
    else:
        if database_key is None:
            database_key = read_pod_key("database_key")
        if owner_key is None:
            owner_key = read_pod_key("owner_key")
        pod_auth_json = None
    if POD_PLUGIN_DNS_ENV in os.environ:
        print(f"Plugin accessible via {os.environ.get(POD_PLUGIN_DNS_ENV)}:8080")

    client = PodClient(
        url=pod_full_address,
        database_key=database_key,
        owner_key=owner_key,
        auth_json=pod_auth_json,
    )
    print(f"pod_full_address={pod_full_address}\nowner_key={owner_key}\n")

    if metadata is not None:
        run = parse_metadata(metadata, remove_container=True)
        create_run_expanded(client, run)
        plugin_run_id = run.id
    else:
        run = client.get(plugin_run_id)
    plugin_config = parse_config(run.config, config_file)

    try:
        run_plugin_from_run_id(plugin_run_id, client, **plugin_config)
    except Exception as e:
        run = client.get(plugin_run_id)
        run.status = RUN_FAILED
        client.update_item(run)
        print(traceback.format_exc(), flush=True)
        raise PluginError("The plugin quit unexpectedly.") from None


@call_parse
def simulate_run_plugin_from_frontend(
    pod_full_address: Param("The pod full address", str) = DEFAULT_POD_ADDRESS,
    database_key: Param("Database key of the pod", str) = None,
    owner_key: Param("Owner key of the pod", str) = None,
    container: Param("Pod container to run frod", str) = None,
    plugin_path: Param("Plugin path", str) = None,
    metadata: Param("metadata file for the PluginRun", str) = None,
    config_file: Param(
        "A plugin configuration, overwrites the configuration of the PluginRun", str
    ) = None,
    account_id: Param("Account id to be used inside the plugin", str) = None,
):
    if database_key is None:
        database_key = read_pod_key("database_key")
    if owner_key is None:
        owner_key = read_pod_key("owner_key")
    params = [pod_full_address, database_key, owner_key]
    if None in params:
        raise ValueError("Missing Pod credentials")

    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key)
    print(f"pod_full_address={pod_full_address}\nowner_key={owner_key}\n")

    if metadata is not None:
        run = parse_metadata(metadata)
        create_run_expanded(client, run)
    else:
        if container is None:
            container = plugin_path.split(".", 1)[0]
        print(f"Inferred '{container}' as plugin container name")
        plugin_module, plugin_name = plugin_path.rsplit(".", 1)
        run = PluginRun(container, plugin_module, plugin_name)

        if account_id is not None:
            account = client.get(account_id)
            run.add_edge("account", account)
            print(f"Using existing {account}")

        client.create(run)

    print(f"Created pluginrun with id {run.id} on {pod_full_address}")

    plugin_dir = run.containerImage
    write_run_info(plugin_dir, run.id)

    print("*Check the pod log/console for debug output.*")
    return run


import http.server
import socketserver
import urllib
from urllib.parse import parse_qs, urlsplit

from pymemri.data.schema import OauthFlow
from pymemri.pod.client import PodClient


def get_request_handler(
    client: PodClient, oauth_token_secret: str
) -> http.server.BaseHTTPRequestHandler:
    """
    This is a factory function that returns a request handler class.

    The returned class will have a reference to the client and oauth_token_secret
    variables that are passed to this function.

    This is needed because the request handler class is instantiated by the
    TCPServer class, and we need to pass the client and oauth_token_secret
    variables to the request handler class.
    """

    class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            params = urlsplit(self.path)
            if params.path == "/oauth":
                args = parse_qs(params.query)
                oauth_verifier = args.get("oauth_verifier")[0]
                oauth_token = args.get("oauth_token")[0]
                response = client.api.oauth1access_token(
                    oauth_token=oauth_token,
                    oauth_verifier=oauth_verifier,
                    oauth_token_secret=oauth_token_secret,
                )
                access_token = response["oauth_token"]
                access_token_secret = response["oauth_token_secret"]
                item = OauthFlow(
                    service="twitter",
                    accessToken=access_token,
                    accessTokenSecret=access_token_secret,
                )
                client.create(item)

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("Authenticated, succesfully created oauth item", "utf-8"))

    return MyHttpRequestHandler


@call_parse
def simulate_twitter_flow(
    pod_full_address: Param("The pod full address", str) = DEFAULT_POD_ADDRESS,
    port: Param("Port to listen on", int) = 3667,
    callback_url: Param("Callback url", str) = "http://localhost:3667/oauth?state=twitter",
    database_key: Param("Database key of the pod", str) = None,
    owner_key: Param("Owner key of the pod", str) = None,
):

    if database_key is None:
        database_key = read_pod_key("database_key")
    if owner_key is None:
        owner_key = read_pod_key("owner_key")
    params = [pod_full_address, database_key, owner_key]
    if None in params:
        raise ValueError("Missing Pod credentials")

    print(f"pod_full_address={pod_full_address}\nowner_key={owner_key}\n")
    client = PodClient(url=pod_full_address, database_key=database_key, owner_key=owner_key)
    run_twitter_oauth_flow(client=client, port=port, callback_url=callback_url)
