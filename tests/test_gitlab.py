from pymemri.template.formatter import gitlab_slugify
def test_gitlab_slugify():

    # Lowercased
    string = "SAMPLE Project"
    assert gitlab_slugify(string) == "sample-project"

    # First/Last Character is not a hyphen
    string = "--sample space project--"
    assert gitlab_slugify(string) == "sample-space-project"

    # Maximum length is 63 bytes
    string = "s"*64
    assert gitlab_slugify(string) == "s"*63

    # Anything not matching [a-z0-9-] is replaced with a -
    string = "sample project"
    assert gitlab_slugify(string) == "sample-project"

    string = "sample_project"
    assert gitlab_slugify(string) == "sample-project"

    string = "01-09-test"
    assert gitlab_slugify(string) == "01-09-test"
