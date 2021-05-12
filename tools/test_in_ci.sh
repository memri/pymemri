#!/usr/bin/env bash
set -euETo pipefail

POD_URL='https://gitlab.memri.io/memri/pod/uploads/fbdc70cd34b8c1a8dfb0acd50c4b7a84/pod-from-docker-v0.2.1-101-gba23ee2'

mkdir res

curl "$POD_URL" -o pod_docker

chmod +x ./pod_docker

RUST_LOG=pod=debug,info \
  ./pod_docker \
  --owners=ANY \
  --insecure-non-tls=0.0.0.0 \
  --insecure-http-headers \
  "$@" &

pid=$!
nbdev_test_nbs --n_workers 1
kill $pid

