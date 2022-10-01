import os
from pathlib import Path


def get_ci_variables(*varnames):
    """
    Gets ci variables from environment, can be set on gitlab in settings -> ci/cd -> variables
    """
    return {varname: os.environ.get(varname) for varname in varnames}


def get_project_root():
    return Path(__file__).parent.parent
