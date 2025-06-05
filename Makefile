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
	source $(ACTIVATE) && $(PIP) install -Ue .[dev,test,docs]

.PHONY: prepdocs
prepdocs: .venv
	source $(ACTIVATE) && python -m cogapp -rcP docs/tutorial.md

.PHONY: html
html: prepdocs .venv README.md docs/*.rst docs/conf.py
	source $(ACTIVATE) && sphinx-build -ab html docs html

.PHONY: format
format:
	ruff format
	ruff check --fix

.PHONY: lint
lint:
	ruff check
	python -m checkdeps --allow-names ick,ick_protocol ick
	python -m cogapp -cP --check --diff docs/tutorial.md
	#mypy --strict --install-types --non-interactive advice_animal

.PHONY: test
test:
	pytest --cov=ick --cov=tests --cov-report=term-missing --cov-report=html
