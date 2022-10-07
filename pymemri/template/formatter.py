import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from string import Template
from typing import Dict, List, Union

import giturlparse
import requests
from fastcore.script import Param, call_parse, store_true
from loguru import logger

import pymemri

TEMPLATE_URL = (
    "https://gitlab.memri.io/memri/plugin-templates/-/archive/dev/plugin-templates-dev.zip"
)
TEMPLATE_BASE_PATH = "plugin-templates-dev"


# If the owner of the repository is one of these groups, the CLI requires an additional `user` argument
GITLAB_GROUPS = ["memri", "plugins"]


def get_remote_url():
    path = Path(".")
    url = subprocess.getoutput("git config --get remote.origin.url")
    if not url:
        raise ValueError(
            f"You can only run this from a initialized gitlab repository, and '{path}' is not an initialized git repository"
        )
    parsed = giturlparse.parse(url)
    repo_url = parsed.url2https
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    return repo_url


def infer_git_info(url):
    parsed = giturlparse.parse(url)
    return parsed.owner, parsed.repo


def download_file(url, fname=None):
    cert_path = Path(pymemri.__file__).parent / "cert" / "gitlab.memri.io.pem"
    r = requests.get(url, stream=True, verify=cert_path)
    fname = url.rsplit("/", 1)[1] if fname is None else fname
    with open(fname, "wb") as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
    return fname


def str_to_identifier(s, lower=True):
    result = re.sub("\W|^(?=\d)", "_", s)
    if lower:
        result = result.lower()
    return result


# https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/utils.rb#L92
def gitlab_slugify(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]", "-", s)[:63]
    s = re.sub(r"(^-+|-+$)", "", s)
    return s


def reponame_to_displayname(reponame: str) -> str:
    return re.sub("[-_]+", " ", reponame).title()


def download_plugin_template(
    template_name: str, url: str = TEMPLATE_URL, base_path: str = TEMPLATE_BASE_PATH
):
    # base_path = Path(base_path) / template_name if url is None else Path(url.rsplit("/", 1)[1].split(".")[0]) / template_name

    zip_path = download_file(url)
    base_path = Path(zip_path.split(".")[0]) / template_name

    with zipfile.ZipFile(zip_path, "r") as f:
        result = {name: f.read(name) for name in f.namelist() if base_path in Path(name).parents}

    if len(result) == 0:
        Path(zip_path).unlink()
        raise ValueError(f"Could not find template: {template_name}")

    result = {
        str(PurePosixPath(k).relative_to(PurePosixPath(base_path))): v.decode("utf-8")
        for k, v in result.items()
        if v
    }
    Path(zip_path).unlink()
    return result


def get_templates(url: str = TEMPLATE_URL) -> List[str]:
    zip_path = download_file(url)

    with zipfile.ZipFile(zip_path, "r") as f:
        files_split = [name.split("/") for name in f.namelist()]
        result = [fn[1] for fn in files_split if fn[-1] == "" and len(fn) == 3]
    return result


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
            logger.info(f"Formatting {filename} -> {new_path}")
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    def get_files(self):
        return [self.format_path(filename) for filename in self.template_dict.keys()]

    def format(self):
        for filename, content in self.template_dict.items():
            self.format_file(filename, content)

    def print_filetree(self):
        previous_prefix = None
        res = "Created the following files"

        for path in sorted(
            [x.relative_to(self.tgt_path) for x in self.get_files()],
            key=lambda item: 100 * str(item).count("/"),
        ):
            n_slashes = str(path).count("/")
            new_prefix = path.parent
            if previous_prefix != new_prefix and str(new_prefix) != ".":
                res = f"{res}\n├── {new_prefix}"
            if n_slashes == 0:
                res = f"{res}\n├── {path}"
            elif n_slashes == 1:
                res = f"{res}\n│   ├── {path.name}"

            previous_prefix = new_prefix

        print(res.strip() + "\n")


def get_template_replace_dict(
    repo_url=None,
    user=None,
    plugin_name=None,
    package_name=None,
    description=None,
    install_requires=None,
    template_name=None,
):
    if repo_url is None:
        repo_url = get_remote_url()

    try:
        repo_owner, repo_name = infer_git_info(repo_url)
    except ValueError:
        url_inf = None
        logger.error(
            "Could not infer git information from current directory, no initialized repository found."
        )

    if repo_url is None:
        repo_url = url_inf

    if user is None:
        if repo_owner in GITLAB_GROUPS:
            user = None
        else:
            user = repo_owner

    if plugin_name is None:
        if repo_name is None:
            plugin_name = None
        else:
            plugin_name = reponame_to_displayname(repo_name)

    if package_name is None:
        if repo_name is None:
            package_name = None
        else:
            package_name = str_to_identifier(repo_name)
    if install_requires is None:
        install_requires = ""
    else:
        install_requires = "\n    ".join(
            [
                x.strip()
                for x in install_requires.split(",")
                if x.strip() != "" and x.strip() not in ["pymemri", "pytest"]
            ]
        )

    if template_name == "classifier_plugin":
        assert package_name is not None
        assert user is not None
        repo_name_gitlab = gitlab_slugify(repo_name)

        # hacky, dont change!
        model_imports_ = (
            f"""
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from """
            + "pymemri.data.loader import load_huggingface_model_for_project"
        )
        model_init = f"""
        model = load_huggingface_model_for_project(project_path="{user}/{repo_name_gitlab}", client=client)
        tokenizer = AutoTokenizer.from_pretrained("distilroberta-base", model_max_length=512)
        self.pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, return_all_scores=True, truncation=True)
        """
        model_predict = """
        return self.pipeline(x)
        """
    else:
        model_imports_ = ""
        model_init = "raise NotImplementedError()"
        model_predict = "raise NotImplementedError()"

    return {
        "user": user,
        "package_name": package_name,
        "plugin_name": plugin_name,
        "repo_name": repo_name,
        "repo_url": repo_url,
        "description": str(description),
        "install_requires": install_requires,
        "model_imports": model_imports_,
        "model_init": model_init,
        "model_predict": model_predict,
    }


def _plugin_from_template(
    list_templates=False,
    user=None,
    repo_url=None,
    plugin_name=None,
    template_name="basic",
    package_name=None,
    description=None,
    target_dir=".",
    verbose=True,
    install_requires="",
    template_url=None,
):
    if list_templates:
        print("Available templates:")
        for template in get_templates():
            print(template)
        return

    template = download_plugin_template(
        template_name, **({"url": template_url} if template_url else {})
    )

    tgt_path = Path(target_dir)
    replace_dict = get_template_replace_dict(
        repo_url=repo_url,
        user=user,
        plugin_name=plugin_name,
        package_name=package_name,
        description=description,
        install_requires=install_requires,
        template_name=template_name,
    )
    logger.debug(replace_dict)

    formatter = TemplateFormatter(template, replace_dict, tgt_path)
    formatter.format()
    if verbose:
        formatter.print_filetree()

    logger.info(f"Created `{replace_dict['plugin_name']}` using the {template_name} template.")


@call_parse
def plugin_from_template(
    list_templates: Param("List available plugin templates", store_true) = False,
    user: Param("Your Gitlab username", str) = None,
    repo_url: Param("The url of your empty Gitlab plugin repository", str) = None,
    plugin_name: Param("Display name of your plugin", str) = None,
    template_name: Param(
        "Name of the template, use `list_templates` to see all available options"
    ) = "basic",
    package_name: Param("Name of your plugin python package", str) = None,
    description: Param("Description of your plugin", str) = None,
    target_dir: Param("Directory to output the formatted template", str) = ".",
    verbose: Param("Should print out dir", bool) = True,
    install_requires: Param(
        "Extra packages to install, provided as comma separated, e.g. pymemri,requests", str
    ) = "",
):
    """
    CLI that downloads and formats a plugin template according to the arguments, and local git repository.

    Args:
        list_templates (Param, optional): If True, only list available templates. Defaults to False.
        user (Param, optional): Your GitLab username. Defaults to None.
        repo_url (Param, optional): The url of your gitlab plugin repository. Defaults to None.
        plugin_name (Param, optional): The name of your plugin. Defaults to None.
        template_name (Param, optional): The name of the template used. To list all options, see `list_templates`.
            Defaults to "basic".
        package_name (Param, optional): The name of the python package of your plugin. Inferred if left blank. Defaults to None.
        description (Param, optional): An optional plugin description. Defaults to None.
        target_dir (Param, optional): Directory where the plugin template is generated. Defaults to ".".
    """
    _plugin_from_template(
        list_templates,
        user,
        repo_url,
        plugin_name,
        template_name,
        package_name,
        description,
        target_dir,
        verbose,
        install_requires,
    )
