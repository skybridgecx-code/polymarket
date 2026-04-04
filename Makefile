PYTHON := .venv/bin/python
PIP := .venv/bin/pip
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy
PYTEST := .venv/bin/pytest

.PHONY: setup test lint typecheck validate scan wallet-backfill detect-copiers orchestrate-refresh api

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

orchestrate-refresh:
	$(PYTHON) -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1

api:
	$(PYTHON) -m uvicorn polymarket_arb.api.main:app --reload
