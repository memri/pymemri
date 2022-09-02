import pytest

from pymemri.gitlab_api import GitlabAPI
from pymemri.pod.client import PodClient
from pymemri.template.formatter import gitlab_slugify


def test_gitlab_slugify():

    # Lowercased
    string = "SAMPLE Project"
    assert gitlab_slugify(string) == "sample-project"

    # First/Last Character is not a hyphen
    string = "--sample space project--"
    assert gitlab_slugify(string) == "sample-space-project"

    # Maximum length is 63 bytes
    string = "s" * 64
    assert gitlab_slugify(string) == "s" * 63

    # Anything not matching [a-z0-9-] is replaced with a -
    string = "sample project"
    assert gitlab_slugify(string) == "sample-project"

    string = "sample_project"
    assert gitlab_slugify(string) == "sample-project"

    string = "01-09-test"
    assert gitlab_slugify(string) == "01-09-test"


def test_gitlab_missing_oauth():
    # Create a random owner/database key pair
    client = PodClient()
    with pytest.raises(RuntimeError):
        gitlab = GitlabAPI(client)


@pytest.mark.skip(
    reason="This test requires a valid Gitlab API token, which is not available in CI"
)
def test_gitlab_project_id():
    owner_key = ""
    database_key = ""
    client = PodClient(owner_key=owner_key, database_key=database_key)
    gitlab = GitlabAPI(client)
    project_id = gitlab.project_id_from_name("test-proj")
