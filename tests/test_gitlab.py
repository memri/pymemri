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


@pytest.mark.skipif(
    os.environ.get("CI_JOB_TOKEN") is None,
    reason="CI_JOB_TOKEN environment variable not set",
)
def test_gitlab_project_id():
    client = PodClient()
    gitlab = GitlabAPI(client)
    project_id = gitlab.project_id_from_name("pymemri", "memri")
    assert project_id == 80
