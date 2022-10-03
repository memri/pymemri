import os

import pytest

from pymemri.gitlab_api import GitlabAPI
from pymemri.pod.client import PodClient
from pymemri.template.formatter import gitlab_slugify


@pytest.mark.parametrize(
    "input,expected",
    [
        ("SAMPLE Project", "sample-project"),
        ("--sample space project--", "sample-space-project"),
        ("s" * 64, "s" * 63),
        ("sample project", "sample-project"),
        ("sample_project", "sample-project"),
        ("01-09-test", "01-09-test"),
    ],
)
def test_gitlab_slugify(input, expected):
    assert gitlab_slugify(input) == expected


@pytest.mark.skip(
    reason="This test requires a valid Gitlab API token, which is not available in CI"
)
def test_gitlab_project_id():
    owner_key = ""
    database_key = ""
    client = PodClient(owner_key=owner_key, database_key=database_key)
    gitlab = GitlabAPI(client)
    project_id = gitlab.project_id_from_name("test-proj")
