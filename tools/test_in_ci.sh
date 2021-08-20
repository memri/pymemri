#!/usr/bin/env bash
set -euETo pipefail

mkdir res
# To update Pod URL:
# * Check out recent pipelines in https://gitlab.memri.io/memri/pod/-/pipelines
# * Pick a pipeline from the `dev` branch if you're developing against `dev`
# * Go to "release" stage job artifacts
# * Copy the URL to the Pod executable
#
# (TODO: shrink the above instruction to a single URL following documentation here
#  https://docs.gitlab.com/ee/ci/pipelines/job_artifacts.html#access-the-latest-job-artifacts-by-url
#  Contributions welcomed!)

# POD_URL='https://gitlab.memri.io/memri/pod/-/jobs/4102/artifacts/file/target/release/pod'
# POD_URL='https://gitlab.memri.io/memri/pymemri/-/raw/ci/pod_ci?inline=false'
POD_URL='https://gitlab.memri.io/memri/pymemri/-/raw/v4/pod_ci?inline=false'

curl "$POD_URL" -o pod_docker

chmod +x ./pod_docker

cp /bin/true ./docker && PATH="$PWD:PATH" && RUST_LOG=pod=debug,info \
  ./pod_docker \
  --owners=ANY \
  --insecure-non-tls=0.0.0.0 \
  --insecure-http-headers \
  "$@" &

pid=$!
nbdev_test_nbs
# nbdev_test_nbs --fname nbs/pod.client.ipynb
kill $pid

