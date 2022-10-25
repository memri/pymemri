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
                response = client.get_oauth1_access_token(
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


def run_twitter_oauth_flow(
    *,
    client: PodClient,
    callback_url: str,
    host: str = "localhost",
    port: int = 3667,
) -> None:
    callback_url = callback_url or f"http://{host}:{port}/oauth?state=twitter"
    response = client.get_oauth1_request_token("twitter", callback_url)

    oauth_token_secret = response["oauth_token_secret"]
    queryParameters = {"oauth_token": response["oauth_token"]}
    encoded = urllib.parse.urlencode(queryParameters)
    print(f"*** \n\nGo to https://api.twitter.com/oauth/authorize?{encoded} \n\n***\n\n")

    socketserver.TCPServer.allow_reuse_address = True
    my_server = socketserver.TCPServer(
        (host, port), get_request_handler(client, oauth_token_secret)
    )

    client.add_to_schema(OauthFlow)
    my_server.handle_request()
