PYTHON := .venv/bin/python
PIP := .venv/bin/pip
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy
PYTEST := .venv/bin/pytest

.PHONY: setup test lint typecheck validate scan wallet-backfill detect-copiers orchestrate-refresh paper-trade review-packet replay-evaluate api future-system-operator-ui-demo future-system-operator-ui-demo-clean

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

paper-trade:
	$(PYTHON) -m polymarket_arb.cli paper-trade --limit 5

review-packet:
	$(PYTHON) -m polymarket_arb.cli review-packet --packet-type opportunities --limit 5

replay-evaluate:
	@echo "replay-evaluate requires explicit baseline and candidate packet paths." >&2
	@exit 1

api:
	$(PYTHON) -m uvicorn polymarket_arb.api.main:app --reload

future-system-operator-ui-demo:
	bash scripts/launch_future_system_operator_ui_demo.sh

future-system-operator-ui-demo-clean:
	@echo "Cleaning demo artifacts: .tmp/future-system-operator-ui-demo"
	@rm -rf .tmp/future-system-operator-ui-demo
	@echo "Done."
