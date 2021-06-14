#!/usr/bin/env bash

export owner="SRANDOMSRANDOMSRANDOM"  # replace with desired owner, or leave as-is for tests
export dbkey=""  # note that the Plugin will not have access to this key, it'll only have `POD_AUTH_JSON`
export container="test"

data=$(cat <<-END
{
    "auth": {
        "type": "ClientAuth",
        "databaseKey": "$dbkey"
    },
    "payload": {
        "createItems": [
            {"type": "Person", "id": "38583224e56e6d2385d36e05af9caa5e"},
            {"type": "StartPlugin", "container": "$container", "targetItemId": "38583224e56e6d2385d36e05af9caa5e"}
        ],
        "updateItems": [],
        "deleteItems": []
    }
}
END
)

echo "abc"
echo $owner
echo "http://localhost:3030/v3/${owner}/bulk"

curl -X POST -H "Content-Type: application/json" --insecure "http://localhost:3030/v3/$owner/bulk" -d "$data"
