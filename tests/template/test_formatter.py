from sys import stdout
from pymemri.template.formatter import TemplateFormatter, download_plugin_template
from pathlib import Path
import tempfile
import subprocess
import os

def test_list_templates():
    result = subprocess.run(["plugin_from_template", "--list_templates"], stdout=subprocess.PIPE)
    result = result.stdout.splitlines()
    assert result[0] == b"Available templates:"
    assert len(result) > 1


def test_formatter():
    template = download_plugin_template("classifier_plugin")
    replace_dict = {
        "user": "test-user",
        "repo_name": "sentiment-plugin",
        "package_name": "sentiment_plugin",
        "plugin_name": "Sentiment Plugin",
        "description": "Predict sentiment on text messages"
    }

    with tempfile.TemporaryDirectory() as result_path:
        print(result_path)
        result_path = Path(result_path)
        formatter = TemplateFormatter(template, replace_dict, result_path)
        formatter.format()
        created_files = [f for f in result_path.rglob("*") if not os.path.isdir(f)]
        
        contents = {}
        for fn in created_files:
            with open(fn, "r") as f:
                contents[str(fn)] = f.read()

    formatter.print_filetree()
    assert len(template) == len(created_files)
