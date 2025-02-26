ifeq ($(OS),Windows_NT)
    ACTIVATE:=.venv/Scripts/activate
else
    ACTIVATE:=.venv/bin/activate
endif

UV:=$(shell uv --version)
ifdef UV
	VENV:=uv venv
	PIP:=uv pip
else
	VENV:=python -m venv
	PIP:=python -m pip
endif

.venv:
	$(VENV) .venv

.PHONY: setup
setup: .venv
	source $(ACTIVATE) && $(PIP) install -Ue .[dev,test]

.PHONY: html
html: .venv README.md docs/*.rst docs/conf.py
	source $(ACTIVATE) && sphinx-build -ab html docs html

.PHONY: format
format:
	ruff format
	ruff check --fix

.PHONY: test
test:
	pytest --cov=ick

.PHONY: lint
lint:
	mypy --strict
