#!/usr/bin/env bash
set -euETo pipefail

export POD_ADDRESS='http://pod:3030/'
nbdev_test_nbs --flags ci