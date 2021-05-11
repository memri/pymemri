# pymemri
> Pymemri is a python client for the memri Personal online datastore (pod). This client can be used to build integrators in python. Integrators connect the information in your Pod. They <b>import your data from external services</b> using <i>Importers</i> (Gmail, WhatsApp, etc.), <b>connect new data to the existing data</b> using <i>indexers</i> (face recognition, spam detection, object detection), and <b>execute actions</b> (sending messages, uploading files).


[![Gitlab pipeline status (self-hosted)](https://img.shields.io/gitlab/pipeline/memri/pymemri/dev?gitlab_url=https%3A%2F%2Fgitlab.memri.io&label=CI&logo=gitlab&style=plastic)](https://gitlab.memri.io/memri/pymemri/-/pipelines/latest)
[![Discourse status](https://img.shields.io/discourse/status?color=00A850&label=Discourse&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAhCAYAAAC4JqlRAAAEhUlEQVR42r2XA5RjyxqFM7Y90ymd6uCNbdu2bdu2bdu2bdu27dmvUtfpk9zu5K6utXZU+Pb/l3IsISlCiFiCiBKS0m4GpdMNxpa5JCmbZFDeQTKWR0oZyfJfF8l5IQVdr6DfDcrwL3qnDM3knKf2GyysIoMacKcSfNAvg7AllNIkvrDDCMJ6uQZRgj9S2Xjpmppgk1MlShRNULrcD6iZvhqM1QkOP5xqvMnTQIFKJQlHZ6WhAQJDrALtrFz/JoNjhLHaXumqwRizjjYlF/S4gt5PZuAst+Fk9lS4UDg9LhRJj9O502B3quTowARs3k18Vusqo/lKJ7yiWafsCrwtwMA9BT6eISWe106DtzUF3jV04kP/Avg0tQo+z6iGj0OK4nXzzDhSMRtyO6Q3E3ftdnuMf8CTJ08eUVXccG+ck3KcVPArARL3q2XS4A/dc+DboT7Ah2XA11X/1JeV+HFxFB6Pr4Y6xTJ4McF7/jP1lLZ3b+RQ2quivqrgz2upqOtIfN3YVkPcwKa6cmwASlXO7vGsMAwjoYar/RFe/fDIvVF/K9dpf1g9A97WDcT3k4NNQN7V52B3JM+R0dSEIKz3n6ece2VypYvJBI5nTKXT/m1755DCtZ68W4hMi1pABDqCmiDs2u/p5yPcK+sSHT1e1EmDj4MK+wL/U0V3tQBp1R2mu4sQoQywPe4Vo6wcp6RdR68WlV8Gep/tDT57CLg9RdBpoLS6y8BD94qFAQKncqfF+/aZ/lx0vmrejRGwL2uJBJXbmmSB9nMZ+OxesUoZuFwqo9rjlf2Bay25NQpyTX3E6LbQbB1MsZjNzXSrwNVymfB1XSu/DYy/MhBsdW1EGnfILAPzTA30JBwX1EHydUt7vw00PtYRtlWNEHHSCbMMTDY1kJcwfex+WdnML/ivrythXVcN9sVdEGnM/iAcyVgfbcBMa41AfJhYyS8Da++OhWVpacSbOR8xuswxux2reDRQmnBcq5UT+LzCJ/hX1S/VljoIWF0DlpUvkLB8syAMIQTxaCA/5bhcMSt+vV3ik4FWx7vo6BPMnoqwi+6bnIb0vEUVjwaaE4EXE2v4BO9+uqeG25a1hWXVa8Sr3cvsLujs1cC0XGnw8+bEEIHvv12A4nuaa7h9RUtYVjxB5JG7Ibh0j/65lDKmVwNbmxX/x+A/v6zCroeTsPX+BLz7uPTP31+9X4z1d8eh7pH2iLS8HKIsLw86b7CK/CUiTjwG7kxttvrbargnA4FKN1d21YAjj6ei9f4+SL+0M6yzh4HMHq73dZxVlRB1RXkdbfhlZcFW14FY0BfhF17QaY/RbQG4zWn2L/kyYyyyVwNZUjoxeHpHFOrVGLJuQyQpVA3WTHkhpB0sZQbEbjEG4WddRvhF55QuqVX+REPDLnqA6L2WICBncc8PLYT8T4PdDPgkki4HkuUpg6QFKsGaOR+ECPTW/ofBWBkN9cGAXxKUfZCMldbAUDdA2D1JaVoNC10D+mlo7J/bLfQM0PuSsMH6mA1OUS6n+iNB+UQF7a8+15aEJLeEsPwfm4dbxw/8yD4AAAAASUVORK5CYII=&server=https%3A%2F%2Fdiscourse.memri.io)](https://discourse.memri.io) 
[![Twitter URL](https://img.shields.io/twitter/url?label=%40YourMemri&logo=twitter&style=plastic&url=https%3A%2F%2Ftwitter.com%2FYourMemri)](https://twitter.com/YourMemri)

This repository is built with [nbdev](https://github.com/fastai/nbdev), which means that the repo structure has a few differences compared to a standard python repo. 

# Documentation

- [pyMemri Documentation](http://memri.docs.memri.io/pymemri/pod.client.html#File-API)
- [Plugin Tutorial](https://blog.memri.io/getting-started-building-a-plugin/)

# Installing

## As a package
```bash
pip install pymemri
```

## Development
To install the Python package, and correctly setup nbdev for development run:
```bash
pip install -e . && nbdev_install_git_hooks
```
The last command configures git to automatically clean metadata from your notebooks before a commit.

# Quickstart

To use the pymemri `PodClient`, we first need to have a pod running. The quickest way to do this is to install from the [pod repo](https://gitlab.memri.io/memri/pod), and run `./examples/run_development.sh` from within that repo.

```
from pymemri.data.schema import *
from pymemri.pod.client import *

class Dog(Item):
    def __init__(self, name, age, id=None, deleted=None):
        super().__init__(id=id, deleted=deleted)
        self.name = name
        self.age = age
    
    @classmethod
    def from_json(cls, json):
        id = json.get("id", None)
        name = json.get("name", None)
        age = json.get("age", None)
        return cls(id=id,name=name,age=age)

client = PodClient()
example_dog = Dog("max", 2)
client.add_to_schema(example_dog)
dog = Dog("bob", 3)
client.create(dog)
```

# Nbdev & Jupyter Notebooks
The Python integrators are written in [nbdev](https://nbdev.fast.ai/) ([video](https://www.youtube.com/watch?v=9Q6sLbz37gk&t=1301s)). With nbdev, it is encouraged to write code in 
[Jupyter Notebooks](https://jupyter.readthedocs.io/en/latest/install/notebook-classic.html). Nbdev syncs all the notebooks in `/nbs` with the python code in `/pymemri`. Tests are written side by side with the code in the notebooks, and documentation is automatically generated from the code and markdown in the notebooks and exported into the `/docs` folder. Check out the [nbdev quickstart](wiki/nbdev_quickstart.md) for an introduction, **watch the video linked above**, or see the [nbdev documentation](https://nbdev.fast.ai/) for a all functionalities and tutorials.
