import os
import re
import sys
import urllib
from getpass import getpass
from pathlib import Path

import requests
from fastprogress.fastprogress import progress_bar
from git import Repo
from loguru import logger

from pymemri.pod.client import PodClient

from .template.formatter import _plugin_from_template, gitlab_slugify

MEMRI_PATH = Path.home() / ".memri"
MEMRI_GITLAB_BASE_URL = "https://gitlab.memri.io"
ACCESS_TOKEN_PATH = Path.home() / ".memri/access_token/access_token.txt"
GITLAB_API_BASE_URL = "https://gitlab.memri.io/api/v4"
DEFAULT_PACKAGE_VERSION = "0.0.1"

TIME_FORMAT_GITLAB = "%Y-%m-%dT%H:%M:%S.%fZ"
PROJET_ID_PATTERN = '(?<=<span class="gl-button-text">Project ID: )[0-9]+(?=</span>)'


class GitlabAPI:
    def __init__(self, client: PodClient = None, request_auth_if_needed: bool = False):
        self.client = client
        self.auth_headers = dict()
        self.auth_params = dict()
        self.auth_initialized = False
        self.request_auth_if_needed = request_auth_if_needed
        self.get_registry_params_headers()

    def init_auth_params(self):
        access_token = self.client.get_oauth2_access_token("gitlab")
        if access_token is None:
            raise RuntimeError(
                "No gitlab access token found in the pod. "
                "Please authenticate with gitlab in the frontend."
            )
        self.auth_params = {"access_token": access_token}

    def get_registry_params_headers(self):
        job_token = os.environ.get("CI_JOB_TOKEN", None)
        if job_token is not None:
            self.auth_initialized = True
            self.auth_headers = {"JOB-TOKEN": job_token}
        elif self.client is not None:
            self.init_auth_params()
            self.auth_initialized = True
        else:
            ACCESS_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            if ACCESS_TOKEN_PATH.is_file():
                self.auth_initialized = True
                with open(ACCESS_TOKEN_PATH, "r") as f:
                    self.auth_headers = {"PRIVATE-TOKEN": f.read()}
            else:
                if self.request_auth_if_needed:
                    print(
                        """
                    The first time you are uploading a model you need to create an access_token
                    at https://gitlab.memri.io/-/profile/personal_access_tokens?name=Model+Access+token&scopes=api
                    Click at the blue button with 'Create personal access token'"
                    """
                    )
                    access_token = getpass(
                        "Then copy your personal access token from 'Your new personal access token', and paste here: "
                    )
                    with open(ACCESS_TOKEN_PATH, "w") as f:
                        f.write(access_token)
                    self.auth_headers = {"PRIVATE-TOKEN": access_token}
                    self.auth_initialized = True

        # test if we are authenticated
        res = self.get(
            f"{GITLAB_API_BASE_URL}/projects", headers=self.auth_headers, params=self.auth_params
        )
        if res.status_code not in [200, 201]:
            logger.error(res.content)
            raise RuntimeError(res.content)

    def write_file_to_package_registry(
        self,
        project_id,
        file_path,
        package_name,
        version=DEFAULT_PACKAGE_VERSION,
        trigger_pipeline=False,
    ):
        file_path = Path(file_path)
        file_name = file_path.name

        url = f"{GITLAB_API_BASE_URL}/projects/{project_id}/packages/generic/{package_name}/{version}/{file_name}"
        logger.info(f"uploading {file_path}")
        it = upload_in_chunks(file_path)
        res = self.put(
            url=url,
            data=IterableToFileAdapter(it),
            headers=self.auth_headers,
            params=self.auth_params,
        )

        if res.status_code not in [200, 201]:
            logger.error(f"Failed to upload {file_path}: {res.content}")
        else:
            logger.info(f"Succesfully uploaded {file_path}")
            if trigger_pipeline:
                self.trigger_pipeline(project_id)

    def _authenticated_request(self, request_function, *args, **kwargs):
        try:
            return request_function(*args, **kwargs)
        except Exception as e:
            logger.error(e)
            if self.auth_params:
                logger.debug("Maybe access_token is expired, trying again with new auth params")
                self.init_auth_params()
                return request_function(*args, **kwargs)
            else:
                raise e

    def get(self, *args, **kwargs):
        return self._authenticated_request(requests.get, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._authenticated_request(requests.post, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._authenticated_request(requests.put, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._authenticated_request(requests.delete, *args, **kwargs)

    def trigger_pipeline(self, project_id):
        url = f"{GITLAB_API_BASE_URL}/projects/{project_id}/pipeline?ref=main"
        res = self.post(url, headers=self.auth_headers, params=self.auth_params)
        if res.status_code not in [200, 201]:
            logger.error("Failed to trigger pipeline")

    def project_id_from_name(self, project_name, username=None):
        iden = gitlab_slugify(project_name)
        username = username or self.get_current_username()
        uri_encoded_name = urllib.parse.quote_plus(f"{username}/{iden}")
        res = self.get(
            f"{GITLAB_API_BASE_URL}/projects/{uri_encoded_name}",
            headers=self.auth_headers,
            params=self.auth_params,
        )

        if res.status_code not in [200, 201]:
            logger.error(res.content)
            raise RuntimeError(f"Failed to get project id for {project_name}")
        project_id = res.json().get("id", None)
        if project_id:
            return project_id
        else:
            raise ValueError(
                f"No plugin found with name {project_name}, make sure to enter the name as specified in the url of the repo"
            )

    def get_project_id_from_project_path_unsafe(self, project_path):
        try:
            res = self.get(f"{MEMRI_GITLAB_BASE_URL}/{project_path}")
            html = str(res.content)
            match = re.search(PROJET_ID_PATTERN, html)
            return match.group()
        except Exception:
            raise ValueError(f"Could not find project with name {project_path}")

    def download_package_file(
        self,
        filename,
        project_path,
        package_name,
        out_dir=None,
        package_version=DEFAULT_PACKAGE_VERSION,
        download_if_exists=False,
    ):

        project_name = str(project_path).split("/")[-1]
        out_dir = out_dir if out_dir is not None else MEMRI_PATH / "projects" / project_name
        out_dir.mkdir(parents=True, exist_ok=True)

        project_id = self.get_project_id_from_project_path_unsafe(project_path)

        file_path = out_dir / filename

        if file_path.exists() and not download_if_exists:
            logger.warning(
                f"{file_path} already exists, and `download_if_exists`==False, using cached version"
            )
            return file_path

        logger.info(f"downloading {filename} from project {project_path}, package {package_name}")

        res = self.get(
            url=f"{GITLAB_API_BASE_URL}/projects/{project_id}/packages/generic/{package_name}/{package_version}/{filename}"
        )
        res.raise_for_status()
        with open(out_dir / filename, "wb") as f:
            logger.info(f"writing {filename} to {out_dir}")
            f.write(res.content)
        return file_path

    def create_repo(self, repo_name, client=None):
        url = f"{GITLAB_API_BASE_URL}/projects/"
        payload = {"name": repo_name}
        res = self.post(url=url, json=payload, headers=self.auth_headers, params=self.auth_params)

        if res.status_code not in [200, 201]:
            raise ValueError(f"failed to create repo:\n {res.text}")
        logger.info(f"created project {repo_name}")

    def get_current_username(self, client=None):
        url = f"{GITLAB_API_BASE_URL}/user/"
        res = self.get(url=url, headers=self.auth_headers, params=self.auth_params)
        if res.status_code not in [200, 201]:
            raise ValueError(f"Could not find current user {res.content}")
        else:
            username = res.json()["username"]
            return username

    # NEVER EXPORT THIS
    def delete_project(self, path_or_id, client=None):
        url_escape_id = urllib.parse.quote(str(path_or_id), safe="")
        url = f"{GITLAB_API_BASE_URL}/projects/{url_escape_id}"
        res = self.delete(url=url, headers=self.auth_headers, params=self.auth_params)
        if res.status_code not in [200, 201, 202]:
            raise ValueError(f"failed to delete repo:\n {res.text}")
        logger.info(f"deleted project {path_or_id}")

    def commit_file(self, project_name, path_in2out, branch="main", client=None):
        project_id = self.project_id_from_name(project_name)
        #     file_out_path_escaped = urllib.parse.quote(file_out_path, safe='')

        actions = []

        for file_in_path, file_out_path in path_in2out.items():
            content = Path(file_in_path).read_text()
            action_payload = {
                "action": "create",
                "file_path": file_out_path,
                "content": content,
            }
            actions.append(action_payload)

        url = f"{GITLAB_API_BASE_URL}/projects/{project_id}/repository/commits"
        payload = {
            "branch": branch,
            "commit_message": "automated commit",
            "content": content,
            "actions": actions,
        }

        res = self.post(url=url, json=payload, headers=self.auth_headers, params=self.auth_params)
        files_in = list(path_in2out.keys())
        if res.status_code not in [200, 201, 202]:
            raise ValueError(f"failed to make commit with files {files_in}:\n {res.text}")
        logger.info(f"committed files {files_in}")

    def write_files_to_git(self, repo, target_dir, **kwargs):
        path_in2out = dict()
        for p in target_dir.rglob("*"):
            if p.is_file():
                path_in_repo = p.relative_to(target_dir)
                path_in2out[str(p)] = str(path_in_repo)
        self.commit_file(str(repo), path_in2out, **kwargs)

    def create_new_project(self, project_name, user=None, template_url=None):
        tmp_dir = Path("/tmp/test") / project_name
        rm_tree(tmp_dir)
        repo_url = (
            f"{MEMRI_GITLAB_BASE_URL}/{user}/{project_name}"
            if user is not None
            else f"{MEMRI_GITLAB_BASE_URL}/plugins/{project_name}"
        )

        _plugin_from_template(
            template_name="classifier_plugin",
            description="A transformer based sentiment analyis plugin",
            install_requires="transformers,sentencepiece,protobuf,torch==1.10.0",
            target_dir=str(tmp_dir),
            repo_url=repo_url,
            verbose=False,
            user=user,
            template_url=template_url,
        )
        self.write_files_to_git(project_name, tmp_dir)


def find_git_repo():
    path = "."
    for i in range(10):
        try:
            repo = Repo(f"{path + ('.' * i)}/")
        except:
            pass
        else:
            break
    if i == 9:
        raise ValueError(f"could not fine git repo in {os.path.abspath('')}")

    repo_name = repo.remotes.origin.url.split(".git")[0].split("/")[-1]
    return repo_name


class upload_in_chunks(object):
    def __init__(self, filename, chunksize=1 << 14):
        self.filename = filename
        self.chunksize = chunksize
        self.totalsize = os.path.getsize(filename)
        self.readsofar = 0

    def __iter__(self):
        n = 100
        pb = progress_bar(range(n))
        pb_iter = iter(pb)
        i = 1
        delta = 1 / n
        next(pb_iter, None)

        with open(self.filename, "rb") as file:
            while True:
                data = file.read(self.chunksize)
                if not data:
                    sys.stderr.write("\n")
                    break
                self.readsofar += len(data)
                percent = self.readsofar * 1e2 / self.totalsize
                while (percent / 100) > i * delta:
                    next(pb_iter, None)
                    i += 1
                yield data
        pb.update_bar(n)

    def __len__(self):
        return self.totalsize


class IterableToFileAdapter(object):
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.length = len(iterable)

    def read(self, size=-1):  # TBD: add buffer for `len(data) > size` case
        return next(self.iterator, b"")

    def __len__(self):
        return self.length


def rm_tree(pth):
    pth = Path(pth)
    for child in pth.glob("*"):
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)

    try:
        pth.rmdir()
    except FileNotFoundError as e:
        pass
