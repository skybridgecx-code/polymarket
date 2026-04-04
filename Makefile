PYTHON := .venv/bin/python
PIP := .venv/bin/pip
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy
PYTEST := .venv/bin/pytest

.PHONY: setup test lint typecheck validate scan wallet-backfill detect-copiers api

setup:
	python3.11 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(PYTEST)

lint:
	$(RUFF) check .

typecheck:
	$(MYPY) src

validate: lint typecheck test

scan:
	$(PYTHON) -m polymarket_arb.cli scan --limit 5

wallet-backfill:
	$(PYTHON) -m polymarket_arb.cli wallet-backfill --limit 10

detect-copiers:
	$(PYTHON) -m polymarket_arb.cli detect-copiers --limit 10

api:
	@echo "api is not implemented until Phase 5." >&2
	@exit 1
