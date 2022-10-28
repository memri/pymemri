from pathlib import Path

from loguru import logger

from ..gitlab_api import DEFAULT_PACKAGE_VERSION, GitlabAPI, find_git_repo

DEFAULT_PLUGIN_MODEL_PACKAGE_NAME = "plugin-model-package"
DEFAULT_PYTORCH_MODEL_NAME = "pytorch_model.bin"
DEFAULT_HUGGINFACE_CONFIG_NAME = "config.json"


def write_huggingface_model_to_package_registry(
    project_name, model, version=DEFAULT_PACKAGE_VERSION, client=None
):
    import torch

    api = GitlabAPI(client=client)
    project_id = api.project_id_from_name(project_name)
    local_save_dir = Path("/tmp")
    torch.save(model.state_dict(), local_save_dir / DEFAULT_PYTORCH_MODEL_NAME)
    model.config.to_json_file(local_save_dir / DEFAULT_HUGGINFACE_CONFIG_NAME)

    for f in [DEFAULT_HUGGINFACE_CONFIG_NAME, DEFAULT_PYTORCH_MODEL_NAME]:
        file_path = local_save_dir / f
        logger.info(
            f"writing {f} to package registry of {project_name} with project id {project_id}"
        )
        api.write_file_to_package_registry(
            project_id,
            file_path,
            package_name=DEFAULT_PLUGIN_MODEL_PACKAGE_NAME,
            version=version,
            trigger_pipeline=False,
        )
    api.trigger_pipeline(project_id=project_id)


def write_model_to_package_registry(model, project_name=None, client=None):
    project_name = project_name if project_name is not None else find_git_repo()
    if type(model).__module__.startswith("transformers"):
        import torch
        import transformers
    if isinstance(model, transformers.PreTrainedModel):
        write_huggingface_model_to_package_registry(project_name, model, client=client)
    else:
        raise ValueError(f"Model type not supported: {type(model)}")


def download_huggingface_model_for_project(
    project_path=None, files=None, download_if_exists=False, client=None
):
    api = GitlabAPI(client=client)
    if files is None:
        files = ["config.json", "pytorch_model.bin"]
    for f in files:
        out_file_path = api.download_package_file(
            f, project_path=project_path, package_name=DEFAULT_PLUGIN_MODEL_PACKAGE_NAME
        )
    return out_file_path.parent


def load_huggingface_model_for_project(
    project_path=None, files=None, download_if_exists=False, client=None
):
    out_dir = download_huggingface_model_for_project(
        project_path, files, download_if_exists, client=client
    )
    from transformers import AutoModelForSequenceClassification

    model = AutoModelForSequenceClassification.from_pretrained(out_dir)
    return model
