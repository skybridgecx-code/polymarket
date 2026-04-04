# Polymarket Arbitrage Research

Official frozen read-only baseline for Polymarket analytics as of Phase 7A.

The repo currently ships:

- read-only Gamma, CLOB, Data API, and market websocket ingestion
- fee-aware opportunity scanning with explicit rejection reasons
- wallet seed discovery and wallet activity ingestion
- explainable lead/lag copier relationship detection
- paper-trade execution plan research and simulated fills
- read-only FastAPI operator routes
- bounded real-time refresh orchestration with lightweight checkpointing

The repo explicitly does not ship:

- trading or order placement
- auth or private key handling
- UI
- background workers
- copy-trading execution
- live order submission
- clustering beyond pairwise relationship scoring
- database or broad persistence layers

## Quick Start

```bash
make setup
source .venv/bin/activate
make validate
python -m polymarket_arb.cli scan --limit 5
```

## Current CLI

```bash
python -m polymarket_arb.cli scan --limit 5
python -m polymarket_arb.cli wallet-backfill --limit 10
python -m polymarket_arb.cli detect-copiers --limit 10
python -m polymarket_arb.cli paper-trade --limit 5
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1
```

All CLI commands emit deterministic JSON shapes. Live values vary because public market data changes.

## Current API

Start the read-only API:

```bash
python -m uvicorn polymarket_arb.api.main:app --reload
```

Available routes:

- `GET /health`
- `GET /opportunities?limit=5`
- `GET /wallets/backfill?limit=10`
- `GET /relationships/copiers?limit=10`

`/health` exposes orchestration and staleness state. The other routes are thin wrappers over existing service-layer logic and keep rejected outputs visible.

## Orchestration And Checkpointing

`orchestrate-refresh` is a bounded refresh pass, not a daemon. It:

- refreshes opportunities through `ScanService`
- refreshes copier reports through `CopierDetectionService`
- derives websocket subscriptions from current opportunity legs
- consumes a bounded number of market websocket messages
- writes a lightweight checkpoint file in `state/`

Default checkpoint file:

- `state/runtime_orchestrator_checkpoint.json`

The checkpoint tracks:

- last scan refresh time
- last relationship refresh time
- last websocket connect and event times
- reconnect and disconnect counts
- subscribed asset ids
- last error
- stale reasons

## Module Boundaries

- `src/polymarket_arb/clients/`: public read-only external clients
- `src/polymarket_arb/ingest/`: normalization only
- `src/polymarket_arb/opportunities/`: opportunity scoring only
- `src/polymarket_arb/execution/`: paper-trade plan generation and simulation only
- `src/polymarket_arb/relationships/`: relationship scoring only
- `src/polymarket_arb/services/`: orchestration of clients and engines
- `src/polymarket_arb/api/`: thin FastAPI route layer
- `src/polymarket_arb/models/`: raw, normalized, opportunity, relationship, and orchestration models

Raw payload handling remains separate from normalization and scoring.

## Validation

Core gate:

```bash
make validate
```

Useful smoke commands:

```bash
python -m polymarket_arb.cli scan --limit 5
python -m polymarket_arb.cli wallet-backfill --limit 10
python -m polymarket_arb.cli detect-copiers --limit 10
python -m polymarket_arb.cli paper-trade --limit 5
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1
python -m uvicorn polymarket_arb.api.main:app --reload
```

## Read Next

- [docs/BASELINE.md](/Users/muhammadaatif/polymarket-arb/docs/BASELINE.md)
- [ARCHITECTURE.md](/Users/muhammadaatif/polymarket-arb/ARCHITECTURE.md)
- [ROADMAP.md](/Users/muhammadaatif/polymarket-arb/ROADMAP.md)
- [CODEX_HANDOFF.md](/Users/muhammadaatif/polymarket-arb/CODEX_HANDOFF.md)
