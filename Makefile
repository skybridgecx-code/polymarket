PYTHON := .venv/bin/python
PIP := .venv/bin/pip
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy
PYTEST := .venv/bin/pytest

.PHONY: setup test lint typecheck validate scan wallet-backfill api

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
	@echo "wallet-backfill is not implemented until Phase 3." >&2
	@exit 1

api:
	@echo "api is not implemented until Phase 5." >&2
	@exit 1

