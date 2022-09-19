.ONESHELL:
SHELL := /bin/bash
TWINE_PASSWORD := $TESTPYPI_TOKEN
TWINE_USERNAME := __token__

release: dist
	twine upload --repository pypi dist/*

test_release: dist
	twine upload --repository testpypi dist/*

dist: clean
	python setup.py sdist bdist_wheel

clean:
	rm -rf dist

make test_install:
	pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pymemri
