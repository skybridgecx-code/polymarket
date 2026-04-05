# Polymarket Arbitrage Research

Controlled read-only Polymarket analytics repo with review-packet and replay evaluation support.

The repo currently ships:

- read-only Gamma, CLOB, Data API, and market websocket ingestion
- fee-aware opportunity scanning with explicit rejection reasons
- wallet seed discovery and wallet activity ingestion
- explainable lead/lag copier relationship detection
- paper-trade execution plan research and simulated fills
- paper-trade policy decisions attached to final simulated results
- review packet generation and replay evaluation
- read-only FastAPI operator routes
- bounded real-time refresh orchestration with lightweight checkpointing

Phase 10A adds operator documentation only. It does not change Python behavior, routes, CLI commands, scoring, policy, or live-trading scope.

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
python -m polymarket_arb.cli review-packet --packet-type opportunities --limit 5
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/baseline.json --candidate-path /tmp/candidate.json
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

Health states are derived from that checkpoint:

- `idle`: no scan or relationship refresh has been written yet
- `ok`: refresh data exists and no stale reasons are active
- `stale`: refresh data exists and one or more stale reasons are active

Current stale reasons are:

- `scan_never_refreshed`
- `scan_refresh_overdue`
- `relationships_never_refreshed`
- `relationship_refresh_overdue`
- `websocket_never_received_event`
- `websocket_event_overdue`
- `last_error_present`

Important current behavior: `status` and `stale` are not identical. A never-run system can still report `status: idle` while carrying never-refreshed stale reasons.

## Operator Runbook

Use the operator runbook for exact checkpoint inspection flow, runtime/env expectations, and bounded packet review workflow:

- [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)

## Module Boundaries

- `src/polymarket_arb/clients/`: public read-only external clients
- `src/polymarket_arb/ingest/`: normalization only
- `src/polymarket_arb/opportunities/`: opportunity scoring only
- `src/polymarket_arb/execution/`: paper-trade plan generation and simulation only
- `src/polymarket_arb/review/`: review packet building and replay evaluation only
- `src/polymarket_arb/relationships/`: relationship scoring only
- `src/polymarket_arb/services/`: orchestration of clients and engines
- `src/polymarket_arb/api/`: thin FastAPI route layer
- `src/polymarket_arb/models/`: raw, normalized, opportunity, relationship, and orchestration models

Raw payload handling remains separate from normalization and scoring.

In the paper-trade path, policy runs after simulation. It records `allow`, `hold`, or `deny` as `policy_decision` on each paper-trade row. Manual override fields are audit fields only and are not operationalized. Circuit-breaker state is recorded and can force `hold`.

Phase 9 added the policy layer. Phase 10A adds only operator documentation and runbook hardening.

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
python -m polymarket_arb.cli review-packet --packet-type opportunities --limit 5
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/baseline.json --candidate-path /tmp/candidate.json
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1
python -m uvicorn polymarket_arb.api.main:app --reload
```

## Read Next

- [docs/BASELINE.md](/Users/muhammadaatif/polymarket-arb/docs/BASELINE.md)
- [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)
- [ARCHITECTURE.md](/Users/muhammadaatif/polymarket-arb/ARCHITECTURE.md)
- [ROADMAP.md](/Users/muhammadaatif/polymarket-arb/ROADMAP.md)
- [CODEX_HANDOFF.md](/Users/muhammadaatif/polymarket-arb/CODEX_HANDOFF.md)
