# Contributing

## Installation
For development, Pymemri has a few extra requirements for linting, code quality, and testing. You can install these extra requirements by including the `dev` tag when installing pymemri:

```
pip install -e .[dev]
```

## Testing
Pymemri uses `pytest` as testing tool. All tests are located in the `tests` folder, and can be run with:

```
pytest tests
```

## Pre-commit

Pymemri uses [pre-commit](https://pre-commit.com/), which configures git hooks for popular code quality tools.

pre-commit is installed along with all dev requirements. To enable the pre-commit hooks for pymemri, run:

```
pre-commit install
```

When the pre-commit is installed, it will check all configured pre-commit hooks when you `git commit`, and give you a warning if it fails.
You can check if everything is configured correctly with:

```
pre-commit run --all-files
```

## Generating the schema

the schema in `pymemri/data/_central_schema.py` is generated from the Memri central schema. To generate a new version of the schema, you can use:

```
bash tools/generate_central_schema.sh
```

## Releasing

To release a new version of pymemri, make sure that __version__ in `pymemri/__init__.py` is updated
and has the format `x.y.z`, where `x` is the major version, `y` is the minor version, and `z` is the patch version.

Then, create a git tag with the same version and of the form `vx.y.z` with "v" infront of the version number.

```
git tag -a vx.y.z -m "xyz feature is released in this tag."
git push origin vx.y.z
```

This will trigger a gitlab CI that will build and publish the new version to pypi.