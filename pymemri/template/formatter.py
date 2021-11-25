# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/template.formatter.ipynb (unless otherwise specified).

__all__ = ['TEMPLATE_URL', 'TEMPLATE_BASE_PATH', 'str_to_identifier', 'download_plugin_template', 'TemplateFormatter',
           'plugin_from_template']

# Cell
from pathlib import Path
from typing import Dict, Union
from fastcore.script import call_parse, Param
import zipfile
import tempfile
import urllib
from string import Template
import re

# Cell
TEMPLATE_URL = "https://gitlab.memri.io/plugins/plugin-templates/-/archive/dev/plugin-templates-dev.zip"
TEMPLATE_BASE_PATH = "plugin-templates-dev"

# Cell
def str_to_identifier(s, lower=True):
    result = re.sub("\W|^(?=\d)", "_", s)
    if lower:
        result = result.lower()
    return result


def download_plugin_template(
    template_name: str, url: str = TEMPLATE_URL, base_path: str = TEMPLATE_BASE_PATH
):
    base_path = str(Path(base_path) / template_name)
    zip_path, _ = urllib.request.urlretrieve(url)
    with zipfile.ZipFile(zip_path, "r") as f:
        result = {name: f.read(name) for name in f.namelist() if base_path in name}
    if len(result) == 0:
        raise ValueError(f"Could not find template: {template_name}")
    result = {k.replace(base_path, "").strip("/"): v.decode("utf-8") for k, v in result.items() if v}
    return result

# Cell
class TemplateFormatter:
    def __init__(
        self,
        template_dict: Dict[str, str],
        replace_dict: Dict[str, str],
        tgt_path: Union[str, Path],
        verbose: bool = False,
    ):
        self.template_dict = template_dict
        self.tgt_path = Path(tgt_path)
        self.replace_dict = replace_dict
        self.verbose = verbose

    def format_content(self, content):
        return Template(content).safe_substitute(self.replace_dict)

    def format_path(self, path):
        new_path = Template(path).safe_substitute(self.replace_dict)
        return self.tgt_path / new_path

    def format_file(self, filename, content):
        new_path = self.format_path(filename)
        new_content = self.format_content(content)
        new_path.parent.mkdir(exist_ok=True, parents=True)
        if self.verbose:
            print(f"Formatting {filename} -> {new_path}")
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    def format(self):
        for filename, content in self.template_dict.items():
            self.format_file(filename, content)

# Cell
@call_parse
def plugin_from_template(
    user: Param("Your Gitlab username", str) = None,
    repo_url: Param("The url of your empty Gitlab plugin repository", str) = None,
    plugin_name: Param("Display name of your plugin", str) = None,
    template_name: Param("Name of the template, see the Plugin Templates repository.") = None,
    package_name: Param("Name of your plugin python package", str) = None,
    model_name: Param("Name of the model used in the indexer", str) = None,
    description: Param("Description of your plugin", str) = None,
    target_dir: Param("Directory to output the formatted template", str) = ".",
):
    if template_name is None:
        print("template name not defined, using the classifier_plugin template.")
        template_name = "classifier_plugin"

    if user is None:
        print("Define your gitlab user name with `--user <username>`")
        return

    if plugin_name is None:
        print("Define your gitlab user name with `--plugin_name <name>`")
        return

    if repo_url is None:
        print("Define your gitlab repository url with `--repo_url <url>`")
        return

    repo_name = repo_url.strip("/").split("/")[-1]

    if package_name is None:
        package_name = str_to_identifier(plugin_name, lower=True)

    if model_name is None:
        model_name = package_name + "_model"

    template = download_plugin_template(template_name)
    tgt_path = Path(target_dir)
    replace_dict = {
        "user": user,
        "package_name": package_name,
        "plugin_name": plugin_name,
        "model_name": model_name,
        "repo_name": repo_name,
        "repo_url": repo_url,
        "description": str(description),
    }

    formatter = TemplateFormatter(template, replace_dict, tgt_path)
    formatter.format()

    print("Created template with:")
    for k, v in replace_dict.items():
        print("{:<15} {:<15}".format(k, v))