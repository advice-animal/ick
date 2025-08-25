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
	source $(ACTIVATE) && python -m cogapp -rcP docs/whole-tutorial.md
	perl -ne 'print if 1../splitme1/' < docs/whole-tutorial.md > docs/getting-started/tutorial.md
	perl -ne 'print if /splitme1/../splitme2/' < docs/whole-tutorial.md > docs/getting-started/writing-tutorial.md
	perl -ne 'print if /splitme2/..1' < docs/whole-tutorial.md > docs/getting-started/testing-tutorial.md

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
	python -m cogapp -cP --check --diff docs/whole-tutorial.md

.PHONY: mypy
mypy:
	python -m mypy --strict --install-types --non-interactive ick tests
	@echo $$(grep -R --include='*.py' '# type: ignore.*# FIX ME' ick tests | wc -l) FIX ME comments remain

.PHONY: test
test:
	pytest --cov=ick --cov=tests --cov-report=term-missing --cov-report=html --cov-context=test

.PHONY: clean
clean:
	rm -rf html htmlcov .coverage
