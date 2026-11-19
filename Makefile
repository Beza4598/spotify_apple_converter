PYTHON ?= python3

develop:  ## install the library in editable mode with development tools
	$(PYTHON) -m pip install -e .[develop]

install:  ## install the library
	$(PYTHON) -m pip install .

lint:  ## check formatting with black and run flake8
	$(PYTHON) -m black --check src tests
	$(PYTHON) -m flake8 src tests

lints: lint

format:  ## format the code with black
	$(PYTHON) -m black src tests

fix: format

annotate:  ## run type checking with mypy
	$(PYTHON) -m mypy src

test:  ## run the tests
	$(PYTHON) -m pytest

tests: test

coverage:  ## run the tests and collect coverage
	$(PYTHON) -m pytest --cov --cov-report=term-missing --cov-report=xml

dist: clean  ## build and check the sdist and wheel
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

publish: dist  ## upload the built package to PyPI
	$(PYTHON) -m twine upload dist/*

clean:  ## remove build and test artifacts
	rm -rf .coverage coverage.xml htmlcov build dist src/*.egg-info .pytest_cache .mypy_cache docs/_build

deep-clean:  ## remove every untracked file
	git clean -fdx

.DEFAULT_GOAL := help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

.PHONY: develop install lint lints format fix annotate test tests coverage dist publish clean deep-clean help
