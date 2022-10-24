import urllib

import requests
from flask import Flask, request

from pymemri.data.schema import OauthFlow
from pymemri.pod.client import PodClient
from pymemri.pod.utils import read_pod_key

app = Flask(__name__)

pod_url = f"http://localhost:3030"

# /me
@app.route("/oauth", methods=["GET"])
def get_results():
    oauth_verifier = request.args.get("oauth_verifier")
    oauth_token = request.args.get("oauth_token")
    endpoint = f"{pod_url}/v4/{owner_key}/oauth1_access_token"
    res = requests.post(
        endpoint,
        json={
            "auth": {"type": "ClientAuth", "databaseKey": db_key},
            "payload": {
                "oauthVerifier": oauth_verifier,
                "oauthToken": oauth_token,
                "oauthTokenSecret": twitterOauthTokenSecret,
            },
        },
    ).json()

    oauthToken = res["oauth_token"]
    oauthTokenSecret = res["oauth_token_secret"]
    item = OauthFlow(
        service="twitter",
        accessToken=oauthToken,
        accessTokenSecret=oauthTokenSecret,
    )
    client.create(item)
    return "Authenticated, succesfully created oauth item"


if __name__ == "__main__":

    # read from local file
    db_key = read_pod_key("database_key")
    owner_key = read_pod_key("owner_key")
    client = PodClient(database_key=db_key, owner_key=owner_key)
    client.add_to_schema(OauthFlow)

    redirectUrl = f"http://localhost:3667/oauth?state=twitter"
    endpoint = f"{pod_url}/v4/{owner_key}/oauth1_request_token"

    res = requests.post(
        endpoint,
        json={
            "auth": {"type": "ClientAuth", "databaseKey": db_key},
            "payload": {"service": "twitter", "callbackUrl": redirectUrl},
        },
    ).json()
    twitterOauthToken = res["oauth_token"]
    twitterOauthTokenSecret = res["oauth_token_secret"]

    queryParameters = {"oauth_token": twitterOauthToken}
    encoded = urllib.parse.urlencode(queryParameters)
    print(f"*** \n\nGo to https://api.twitter.com/oauth/authorize?{encoded} \n\n***\n\n")

    app.run(port=3667)
