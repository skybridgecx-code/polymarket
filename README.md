# Polymarket Arbitrage Research

Read-only Polymarket analytics infrastructure for finding candidate dislocations and, later, explainable wallet lead-lag patterns.

## Phase Boundary

This repo is currently scoped to Phase 1 only:

- Python project foundation
- typed config
- public Gamma and CLOB read clients
- raw and normalized market models
- deterministic `scan` CLI command
- unit tests for config and normalization

Explicitly out of scope in this phase:

- trading or order placement
- wallet analytics
- API server
- WebSocket ingestion
- real-time refresh orchestration

## Quick Start

```bash
make setup
source .venv/bin/activate
make validate
python -m polymarket_arb.cli scan --limit 5
```

## CLI

```bash
python -m polymarket_arb.cli scan --limit 5
```

The `scan` command fetches active Gamma events, filters out closed markets, reads current CLOB books for each token, and prints deterministic JSON containing:

- event slug
- market count
- market question
- token ids
- best bid and best ask per token

## Layout

```text
src/polymarket_arb/
  cli.py
  config.py
  logging.py
  clients/
  ingest/
  models/
  services/
tests/
  fixtures/
  unit/
```

## Quality Gates

- `make lint`
- `make typecheck`
- `make test`
- `make validate`

## Notes

- Gamma payloads currently return several array-like fields as JSON-encoded strings.
- Gamma event filtering is not sufficient by itself; market-level normalization also drops closed markets.
- CLOB orderbook asks are normalized by price rather than trusting response order.

