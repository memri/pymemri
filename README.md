# Pymemri
> Pymemri is a python library for creating <b>Plugins</b> for the Memri Personal online datastore <a href='https://gitlab.memri.io/memri/pod'>(pod)</a>. Pymemri has a PodClient to communicate with the pod, and tools to build and test plugins.


[![Gitlab pipeline status (self-hosted)](https://img.shields.io/gitlab/pipeline/memri/pymemri/dev?gitlab_url=https%3A%2F%2Fgitlab.memri.io&label=CI&logo=gitlab&style=plastic)](https://gitlab.memri.io/memri/pymemri/-/pipelines/latest)
[![Discord](https://img.shields.io/discord/799216875480678430?color=blue&label=Discord&logo=discord&style=plastic)](https://discord.gg/BcRfajJk4k)
[![Twitter URL](https://img.shields.io/twitter/url?label=%40YourMemri&logo=twitter&style=plastic&url=https%3A%2F%2Ftwitter.com%2FYourMemri)](https://twitter.com/YourMemri)
<a href="https://pypi.org/project/pymemri/"><img src="https://pepy.tech/badge/pymemri" /></a>

Plugins connect and add the information to your Pod. Plugins that <b>import your data from external services</b> are called **Importers** (Gmail, WhatsApp, etc.). Plugins that <b>connect new data to the existing data</b> are called  **indexers** (face recognition, spam detection, object detection, etc.). Lastly there are plugins that <b>execute actions</b> (sending messages, uploading files). This repository is built with [nbdev](https://github.com/fastai/nbdev), which means that the repo structure has a few differences compared to a standard python repo. 

## Installing

### As a package
```bash
pip install pymemri
```

### Development
To install the Python package, and correctly setup nbdev for development run:
```bash
pip install -e . && nbdev_install_git_hooks
```
The last command configures git to automatically clean metadata from your notebooks before a commit.

## Quickstart: Pod Client

All interaction between plugins and the pod goes via the Pymemri `PodClient`. To use this client in development, we first need to have a pod running locally. The quickest way to do this is to install from the [pod repo](https://gitlab.memri.io/memri/pod), and run `./examples/run_development.sh`.

If you have a running pod, you can define and add your own item definitions:

```python
from pymemri.data.itembase import Item
from pymemri.pod.client import PodClient

class Dog(Item):
    properties = Item.properties + ["name", "age"]

    def __init__(self, name: str = None, age: int = None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.age = age

# Connect to the pod and add the Dog item definition
client = PodClient()
client.add_to_schema(Dog)

# Add a Dog to the pod
dog = Dog("bob", 3)
client.create(dog)
```

## Quickstart: Running a plugin

After installation, users can use the plugin CLI to manually run a plugin. For more information on how to build a plugin, see `run_plugin`.

<b>With the pod running, run in your terminal|: </b>

```bash
store_keys
run_plugin --metadata "example_plugin.json"
```

This stores a random owner key and database key on your disk for future use, and runs the pymemri example plugin. If everything works correctly, the output should read `Plugin run success.`

## Docs

[pymemri docs](https://memri.docs.memri.io/docs.memri.io/component-architectures/plugins/readme/)

## Nbdev & Jupyter Notebooks
The Python integrators are written in [nbdev](https://nbdev.fast.ai/) ([video](https://www.youtube.com/watch?v=9Q6sLbz37gk&t=1301s)). With nbdev, it is encouraged to write code in 
[Jupyter Notebooks](https://jupyter.readthedocs.io/en/latest/install/notebook-classic.html). Nbdev syncs all the notebooks in `/nbs` with the python code in `/pymemri`. Tests are written side by side with the code in the notebooks, and documentation is automatically generated from the code and markdown in the notebooks and exported into the `/docs` folder. Check out the [nbdev quickstart](wiki/nbdev_quickstart.md) for an introduction, **watch the video linked above**, or see the [nbdev documentation](https://nbdev.fast.ai/) for a all functionalities and tutorials.
