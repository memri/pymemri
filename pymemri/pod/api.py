import fnmatch
import json
import logging
import os
import platform
import socket
import urllib
from collections import deque
from hashlib import sha256
from typing import Any, Deque, Dict, Generator, List, Optional, Union

import requests
from loguru import logger
from urllib3.connection import HTTPConnection

from .graphql_utils import GQLQuery

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib").setLevel(logging.WARNING)
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
)

DEFAULT_POD_ADDRESS = os.environ.get("POD_ADDRESS") or "http://localhost:3030"
POD_VERSION = "v4"
POD_ALLOWED_ORIGINS = os.environ.get("POD_ALLOWED_ORIGINS", "*").split(",")


class PodError(Exception):
    def __init__(self, status=None, message=None, **kwargs) -> None:
        super().__init__(status, message, **kwargs)
        self.status = status
        self.message = message

    def __str__(self) -> str:
        return " ".join([str(a) for a in self.args if a])


def get_platform_specific_keepalive_option():
    if platform.system() == "Darwin":
        return (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    else:
        return (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)


class PodAPI:
    def __init__(
        self,
        database_key: str,
        owner_key: str,
        url: str = DEFAULT_POD_ADDRESS,
        version: str = POD_VERSION,
        auth_json: dict = None,
        verbose: bool = True,
    ) -> None:
        self._check_origin(url)

        self.verbose = verbose
        self.database_key = database_key
        self.owner_key = owner_key
        self.version = version
        self._url = url
        self.base_url = f"{url}/{version}/{self.owner_key}"
        self.auth_json = self._create_auth(auth_json)

        # Class uses requests Session to communicate with the POD.
        # That creates a pool of TCP connections, over which HTTP requests
        # with Keep-Alive header are sent. While idle, there is no traffic
        # on those connections, that gets detected by the network balancer
        # of the AWS infrastructure and makes those connection dropped,
        # resulting with "connection reset by peer", or similar errors
        # visible on the client side.
        # Enabling TCP keep-alive packets resets the network balancer idle timer
        # resulting in persistent connection as it was originally intended.
        HTTPConnection.default_socket_options = HTTPConnection.default_socket_options + [
            # Enable TCP keepalive packet transmission
            (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
            # Start sending after 60 sec of idleness
            get_platform_specific_keepalive_option(),
            # Send keep-alive at 60 sec interval
            (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 60),
            # Close connection after 5 failed keep-alive pings (5 minutes)
            (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5),
        ]

        self.session = requests.Session()

    def _check_origin(self, url):
        for origin in POD_ALLOWED_ORIGINS:
            if fnmatch.fnmatch(url, origin):
                return

        raise PodError(
            403,
            f"Trying to create POD API client with callback url {url} that is outside allowed origins {POD_ALLOWED_ORIGINS}",
        )

    def _create_auth(self, auth_json: dict = None) -> dict:
        if auth_json is not None:
            return {"type": "PluginAuth", **auth_json}
        else:
            return {"type": "ClientAuth", "databaseKey": self.database_key}

    def create_account(self):
        response = self.session.post(
            f"{self._url}/{self.version}/account",
            json={"ownerKey": self.owner_key, "databaseKey": self.database_key},
        )
        # if response.status_code != 200:
        #     raise PodError(response.status_code, response.text)

    def test_connection(self) -> bool:
        try:
            res = self.session.get(self._url)
            if self.verbose:
                logger.info("Successfully connected to pod")
            return True
        except requests.exceptions.RequestException as e:
            logger.error("Could no connect to backend")
            return False

    @property
    def pod_version(self) -> dict:
        response = self.session.get(f"{self._url}/version")
        if response.status_code != 200:
            raise PodError(response.status_code, response.text)
        return response.json()

    def post(self, endpoint: str, payload: Any) -> Any:
        body = {"auth": self.auth_json, "payload": payload}
        response = self.session.post(f"{self.base_url}/{endpoint}", json=body)
        if response.status_code != 200:
            raise PodError(response.status_code, response.text)
        return response

    def get_item(self, uid: str) -> dict:
        return self.post("get_item", uid).json()

    def create_item(self, item: dict) -> str:
        return self.post("create_item", item).json()

    def update_item(self, item: dict) -> list:
        return self.post("update_item", item).json()

    def get_edges(
        self, uid: str, direction: str = "Outgoing", expand_items: bool = True
    ) -> List[dict]:
        payload = {"item": uid, "direction": direction, "expandItems": expand_items}
        return self.post("get_edges", payload).json()

    def create_edge(self, edge: dict) -> str:
        return self.post("create_edge", edge).json()

    def delete_item(self, uid) -> list:
        return self.post("delete_item", uid).json()

    def delete_edge(self, edge: dict) -> str:
        return self.post("delete_edge_by_source_target", edge).json()

    def delete_file(self, id: str) -> str:
        return self.post("delete_file", {"id": id}).json()

    def search(self, query: dict) -> List[dict]:
        return self.post("search", query).json()

    def search_paginate(self, query: dict, limit: int = 32, even_page_size=True) -> Generator:
        """
        The Pod returns uneven page sizes when paginating, which can be an issue for some applications.
        `search_paginate` wraps the pagination, and always returns pages of size `limit` by storing overflow items
        in a queue.
        """
        paginator = self._paginate(query, limit)

        if not even_page_size:
            yield from paginator

        remaining: Deque[Dict[str, Any]] = deque()
        while True:
            if len(remaining) >= limit:
                yield [remaining.popleft() for _ in range(limit)]
            if len(remaining) < limit:
                try:
                    remaining.extend(next(paginator))
                except StopIteration:
                    break

        while len(remaining):
            yield [remaining.popleft() for _ in range(min(limit, len(remaining)))]

    def _paginate(self, query: dict, limit: int = 32) -> Generator:
        if (
            "_limit" in query
            or "dateServerModified" in query
            or "dateServerModified>=" in query
            or "dateServerModified<" in query
        ):
            raise ValueError("Cannot paginate query that contains a date or limit.")
        if "_sortOrder" in query:
            raise NotImplementedError("Only 'Asc' order is supported.")

        query = {**query, "_limit": limit}
        response = self.search(query)
        if not len(response):
            return
            yield

        offset = 0
        query = {**query, "_limit": limit}

        while True:
            query["_offset"] = offset

            response = self.search(query)
            if not len(response):
                break

            offset += limit
            yield response

    def bulk(
        self,
        create_items: List[dict] = None,
        update_items: List[dict] = None,
        create_edges: List[dict] = None,
        delete_items: List[str] = None,
        search: List[dict] = None,
    ) -> Dict[str, Any]:
        payload = {
            "createItems": create_items,
            "updateItems": update_items,
            "createEdges": create_edges,
            "deleteItems": delete_items,
            "search": search,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.post("bulk", payload).json()

    def graphql(
        self, query: Union[str, GQLQuery], variables: Optional[Dict[str, Any]] = None
    ) -> List[dict]:
        if isinstance(query, str):
            query = GQLQuery(query)
        query.format(variables)
        return self.post("graphql", query.data).json()

    def oauth(self, service: str, callback_url: str):
        payload = {"service": service, "callbackUrl": callback_url}
        return self.post("oauth", payload).json()

    def upload_file(self, file: bytes) -> Any:
        if self.auth_json.get("type") == "PluginAuth":
            # alternative file upload for plugins, with different authentication
            return self.upload_file_b(file)

        sha = sha256(file).hexdigest()
        result = self.session.post(
            f"{self.base_url}/upload_file/{self.database_key}/{sha}", data=file
        )
        if result.status_code != 200:
            raise PodError(result.status_code, result.text)

        return result

    def upload_file_b(self, file: bytes) -> Any:
        sha = sha256(file).hexdigest()
        auth = urllib.parse.quote(json.dumps(self.auth_json))
        result = self.session.post(f"{self.base_url}/upload_file_b/{auth}/{sha}", data=file)
        if result.status_code != 200:
            raise PodError(result.status_code, result.text)

        return result

    def get_file(self, sha: str) -> bytes:
        return self.post("get_file", {"sha256": sha}).content

    def send_email(self, to: str, subject: str = "", body: str = "") -> Any:
        payload = {"to": to, "subject": subject, "body": body}
        return self.post("send_email", payload)

    def send_trigger_status(self, item_ids: List[str], trigger_id: str, status: str) -> Any:
        payload = {"item_ids": item_ids, "trigger_id": trigger_id, "status": status}
        return self.post("trigger/status", payload)

    def oauth2get_access_token(
        self,
        platform: str,
    ) -> Dict:
        return self.post(
            "oauth2/access_token",
            {"platform": platform},
        ).json()

    def oauth2authorize(
        self, *, platform: str, code: str, redirect_uri: str, pkce_verifier: str
    ) -> Dict[str, str]:
        return self.post(
            "oauth2/authorize",
            {
                "platform": platform,
                "authCode": code,
                "redirectUri": redirect_uri,
                "pkceVerifier": pkce_verifier,
            },
        ).json()

    def oauth2get_authorization_url(
        self, platform: str, scopes: str, redirect_uri: str
    ) -> Dict[str, str]:
        return self.post(
            "oauth2/auth_url",
            {
                "platform": platform,
                "scopes": scopes,
                "redirectUri": redirect_uri,
            },
        ).json()

    def oauth1_request_token(self, platform: str, callback_url: str) -> Any:
        return self.post(
            "oauth1_request_token", {"service": platform, "callbackUrl": callback_url}
        ).json()

    def oauth1_access_token(self, *, oauth_token, oauth_token_secret, oauth_verifier) -> Any:
        return self.post(
            "oauth1_access_token",
            {
                "oauthVerifier": oauth_verifier,
                "oauthToken": oauth_token,
                "oauthTokenSecret": oauth_token_secret,
            },
        ).json()

    def plugin_status(self, plugins: List[str]) -> Any:
        return self.post("plugin/status", {"plugins": plugins}).json()

    def plugin_api(self, plugin_id: str) -> Any:
        return self.post("plugin/api", {"id": plugin_id}).json()

    def plugin_api_call(
        self,
        plugin_id: str,
        method: str,
        endpoint: str,
        query: Dict[str, Any] = None,
        jsonBody: Dict[str, Any] = None,
    ) -> Any:
        payload = {
            "id": plugin_id,
            "method": method,
            "endpoint": endpoint,
            "query": query,
            "jsonBody": jsonBody,
        }

        return self.post("plugin/api/call", payload).json()
