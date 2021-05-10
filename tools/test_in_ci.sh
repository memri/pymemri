#!/usr/bin/env bash
set -euETo pipefail

# curl https://gitlab.memri.io/memri/pod/uploads/83961119f78969e6accdd0453f4dfbc2/pod-from-docker-v0.2.0-9-ga68dee2 -o pod_docker
# curl https://gitlab.memri.io/memri/pod/uploads/1a3852b55d4aa9345b2330181b3ca55e/pod-from-docker-v0.2.1-31-g1abd674 -o pod_docker

mkdir res
# required for pod executable
sudo apt-get install libc6

curl https://gitlab.memri.io/memri/pod/-/jobs/4102/artifacts/raw/target/release/pod -o pod_docker
curl https://gitlab.memri.io/memri/pod/-/raw/dev/res/autogenerated_database_schema.json -o res/autogenerated_database_schema.json

chmod +x ./pod_docker
chmod +x ./res/autogenerated_database_schema.json

RUST_LOG=pod=debug,info \
  ./pod_docker \
  --owners=ANY \
  --insecure-non-tls=0.0.0.0 \
  --insecure-http-headers \
  "$@" &

pid=$!
nbdev_test_nbs --n_workers 1
kill $pid

