# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/data.loader.ipynb (unless otherwise specified).

__all__ = ['MEMRI_PATH', 'MEMRI_GITLAB_BASE_URL', 'ACCESS_TOKEN_PATH', 'GITLAB_API_BASE_URL',
           'DEFAULT_PLUGIN_MODEL_PACKAGE_NAME', 'DEFAULT_PYTORCH_MODEL_NAME', 'DEFAULT_HUGGINFACE_CONFIG_NAME',
           'DEFAULT_PACKAGE_VERSION', 'TIME_FORMAT_GITLAB', 'PROJET_ID_PATTERN', 'find_git_repo',
           'get_registry_api_key', 'upload_in_chunks', 'IterableToFileAdapter', 'write_file_to_package_registry',
           'project_id_from_name', 'get_project_id_from_project_path_unsafe',
           'write_huggingface_model_to_package_registry', 'write_model_to_package_registry', 'download_package_file',
           'download_huggingface_model_for_project', 'load_huggingface_model_for_project']

# Cell
from fastprogress.fastprogress import progress_bar
from pathlib import Path
import requests
import os, sys
from getpass import getpass
from datetime import datetime
from git import Repo
import re

# Cell
MEMRI_PATH = Path.home() / ".memri"
MEMRI_GITLAB_BASE_URL = "https://gitlab.memri.io"
ACCESS_TOKEN_PATH = Path.home() / ".memri/access_token/access_token.txt"
GITLAB_API_BASE_URL = "https://gitlab.memri.io/api/v4"
DEFAULT_PLUGIN_MODEL_PACKAGE_NAME = "plugin-model-package"
DEFAULT_PYTORCH_MODEL_NAME = "pytorch_model.bin"
DEFAULT_HUGGINFACE_CONFIG_NAME = "config.json"
DEFAULT_PACKAGE_VERSION = "0.0.1"

TIME_FORMAT_GITLAB = '%Y-%m-%dT%H:%M:%S.%fZ'
PROJET_ID_PATTERN = '(?<=<span class="gl-button-text">Project ID: )[0-9]+(?=</span>)'

# Cell
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

    repo_name = repo.remotes.origin.url.split('.git')[0].split('/')[-1]
    return repo_name

# Cell
def get_registry_api_key():
    ACCESS_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    if ACCESS_TOKEN_PATH.is_file():
        with open(ACCESS_TOKEN_PATH, "r") as f:
            return f.read()
    else:
        print(f"""
        The first time you are uploading a model you need to create an access_token
        at https://gitlab.memri.io/-/profile/personal_access_tokens?name=Model+Access+token&scopes=api
        Click at the blue button with 'Create personal access token'"
        """)
        access_token = getpass("Then copy your personal access token from 'Your new personal access token', and paste here: ")
        with open(ACCESS_TOKEN_PATH, "w") as f:
            f.write(access_token)
        return access_token

# Cell
class upload_in_chunks(object):
    def __init__(self, filename, chunksize=1 << 13):
        self.filename = filename
        self.chunksize = chunksize
        self.totalsize = os.path.getsize(filename)
        self.readsofar = 0

    def __iter__(self):
        n = 1000
        pb = progress_bar(range(n))
        pb_iter = iter(pb)
        i = 1
        delta = 1 / n

        with open(self.filename, 'rb') as file:
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

    def read(self, size=-1): # TBD: add buffer for `len(data) > size` case
        return next(self.iterator, b'')

    def __len__(self):
        return self.length

# Cell
def write_file_to_package_registry(project_id, file_path, api_key, version=DEFAULT_PACKAGE_VERSION):
    file_path = Path(file_path)
    file_name = file_path.name

    url = f"{GITLAB_API_BASE_URL}/projects/{project_id}/packages/generic/{DEFAULT_PLUGIN_MODEL_PACKAGE_NAME}/{version}/{file_name}"
    print(f"uploading {file_path}")
    it = upload_in_chunks(file_path, 10)
    res = requests.put(url=url, data=IterableToFileAdapter(it),
                     headers={"PRIVATE-TOKEN": api_key})

    if res.status_code not in [200, 201]:
        print(f"Failed to upload {file_path}: {res.content}")
    else:
        print(f"Succesfully uploaded {file_path}")

# Cell
def project_id_from_name(project_name, api_key, job_token=None):
    if api_key:
        headers = {"PRIVATE-TOKEN": api_key}
    else:
        headers = {"JOB-TOKEN": job_token}
    res = requests.get(f"{GITLAB_API_BASE_URL}/projects",
                       headers=headers,
                       params={
                           "owned": True,
                           "search": project_name
                       })
    res =  [x.get("id") for x in res.json()]
    if len(res) == 0:
        raise ValueError(f"No plugin found with name {project_name}")
    else:
        return res[0]

# Cell
def get_project_id_from_project_path_unsafe(project_path):
    try:
        res = requests.get(f"{MEMRI_GITLAB_BASE_URL}/{project_path}")
        html = str(res.content)
        match = re.search(PROJET_ID_PATTERN, html)
        return match.group()
    except Exception:
        raise ValueError(f"Could not find project with name {project_path}")

# Cell
def write_huggingface_model_to_package_registry(project_name, model):
    import torch
    api_key = get_registry_api_key()
    project_id = project_id_from_name(project_name, api_key)
    local_save_dir = Path("/tmp")
    torch.save(model.state_dict(), local_save_dir / DEFAULT_PYTORCH_MODEL_NAME)
    model.config.to_json_file(local_save_dir / DEFAULT_HUGGINFACE_CONFIG_NAME)

    for f in [DEFAULT_HUGGINFACE_CONFIG_NAME, DEFAULT_PYTORCH_MODEL_NAME]:
        file_path = local_save_dir / f
        print(f"writing {f} to package registry of {project_name} with project id {project_id}")
        write_file_to_package_registry(project_id, file_path, api_key)

# Cell
def write_model_to_package_registry(model, project_name=None):
    project_name = project_name if project_name is not None else find_git_repo()
    if type(model).__module__.startswith("transformers"):
        import transformers
        import torch
    if isinstance(model, transformers.PreTrainedModel):
        write_huggingface_model_to_package_registry(project_name, model)
    else:
        raise ValueError(f"Model type not supported: {type(model)}")

# Cell
def download_package_file(filename, project_path=None, out_dir=None, package_name=DEFAULT_PLUGIN_MODEL_PACKAGE_NAME,
                          package_version=DEFAULT_PACKAGE_VERSION, download_if_exists=False):
#     if project_name is None:
#         try:
#             project_name = find_git_repo()
#         except Exception as e:
#             raise ValueError("no project name provided, but could also not find a git repo to infer project name") from None
    project_name = str(project_path).split("/")[-1]
    out_dir = out_dir if out_dir is not None else MEMRI_PATH / "projects" / project_name
    out_dir.mkdir(parents=True, exist_ok=True)
#     if os.environ.get("CI", False):
#         api_key = get_registry_api_key()
#         job_token = None
#     else:
#         api_key=None
#         job_token = os.environ.get("CI_JOB_TOKEN")

    project_id = get_project_id_from_project_path_unsafe(project_path)

#     project_id = project_id_from_name(project_name, api_key, job_token)
    file_path = out_dir / filename

    if file_path.exists() and not download_if_exists:
        print(f"{file_path} already exists, and `download_if_exists`==False, using cached version")
        return out_dir

    print(f"downloading {filename} from project {project_path}, package {package_name}")

    res = requests.get(
        url=f"{GITLAB_API_BASE_URL}/projects/{project_id}/packages/generic/{package_name}/{package_version}/{filename}"
    )
    res.raise_for_status()
    with open(out_dir / filename, "wb") as f:
        print(f"writing {filename} to {out_dir}")
        f.write(res.content)
    return file_path

# Cell
def download_huggingface_model_for_project(project_path=None, files=None, download_if_exists=False):
    if files is None:
        files = ["config.json", "pytorch_model.bin"]
    for f in files:
        out_file_path = download_package_file(f, project_path=project_path)
    return out_file_path.parent

# Cell
def load_huggingface_model_for_project(project_path=None, files=None, download_if_exists=False):
    out_dir = download_huggingface_model_for_project(project_path, files, download_if_exists)
    from transformers import AutoModelForSequenceClassification
    model = AutoModelForSequenceClassification.from_pretrained("distilroberta-base", num_labels=10)
    return model