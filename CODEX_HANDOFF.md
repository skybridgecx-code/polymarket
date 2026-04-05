# Codex Handoff

## Current Status

The repo now includes the shipped Phase 9 paper-trade policy layer, the Phase 10A operator runbook/checkpoint inspection docs, the Phase 10B operator workflow examples/review discipline docs, and the Phase 10C operator checklist/failure-mode docs.

Shipped and in scope:

- read-only market and event ingestion
- fee-aware opportunity scanning
- wallet seed discovery and activity ingestion
- explainable lead/lag copier detection
- paper-trade execution plan generation and simulated fills
- policy decisions attached to final paper-trade rows
- deterministic review packet generation and replay comparison
- read-only FastAPI operator API
- bounded real-time refresh orchestration with checkpointing

Not shipped:

- trading or order placement
- auth or private key work
- UI
- broad persistence or database work
- background workers
- execution automation
- live order submission

Phase 9 policy work did not add:

- new routes
- new CLI commands
- live trading behavior
- new review/replay features

Phase 10A docs work did not add:

- Python behavior changes
- new routes
- new CLI commands
- scoring changes
- policy changes
- live trading behavior

Phase 10B docs work did not add:

- Python behavior changes
- new routes
- new CLI commands
- scoring changes
- policy changes
- live trading behavior

Phase 10C docs work did not add:

- Python behavior changes
- new routes
- new CLI commands
- scoring changes
- policy changes
- live trading behavior

## Read First

- [README.md](/Users/muhammadaatif/polymarket-arb/README.md)
- [ARCHITECTURE.md](/Users/muhammadaatif/polymarket-arb/ARCHITECTURE.md)
- [ROADMAP.md](/Users/muhammadaatif/polymarket-arb/ROADMAP.md)
- [docs/BASELINE.md](/Users/muhammadaatif/polymarket-arb/docs/BASELINE.md)
- [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)

## Operator Commands

Validation:

```bash
make validate
```

CLI:

```bash
python -m polymarket_arb.cli scan --limit 5
python -m polymarket_arb.cli wallet-backfill --limit 10
python -m polymarket_arb.cli detect-copiers --limit 10
python -m polymarket_arb.cli paper-trade --limit 5
python -m polymarket_arb.cli review-packet --packet-type opportunities --limit 5
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/baseline.json --candidate-path /tmp/candidate.json
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1
```

API:

```bash
python -m uvicorn polymarket_arb.api.main:app --reload
```

Routes:

- `GET /health`
- `GET /opportunities`
- `GET /wallets/backfill`
- `GET /relationships/copiers`

## Checkpoint Contract

Default checkpoint path:

- `state/runtime_orchestrator_checkpoint.json`

The file is a lightweight JSON checkpoint used by `RefreshOrchestratorService`. It is the only restart-safety mechanism currently shipped. Treat it as operational state, not as a historical warehouse.

Current health states derived from that checkpoint are:

- `idle`
- `ok`
- `stale`

Current stale reasons are:

- `scan_never_refreshed`
- `scan_refresh_overdue`
- `relationships_never_refreshed`
- `relationship_refresh_overdue`
- `websocket_never_received_event`
- `websocket_event_overdue`
- `last_error_present`

Use the runbook for exact checkpoint inspection and operator review flow:

- [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)

Current command-selection guidance is:

- `orchestrate-refresh` for bounded refresh plus checkpoint/health inspection
- `paper-trade` for current simulated execution rows
- `review-packet` for deterministic subject-type packet export
- `replay-evaluate` for packet-to-packet comparison only

Current failure-mode quick reference covers:

- `scan_never_refreshed`
- `scan_refresh_overdue`
- `relationships_never_refreshed`
- `relationship_refresh_overdue`
- `websocket_never_received_event`
- `websocket_event_overdue`
- `last_error_present`
- `websocket_consumer_exited_without_messages` via `last_error`

## Guardrails For Future Phases

- stay read-only unless a future phase explicitly changes that boundary
- keep paper-trade simulation separate from any future live-capable code path
- keep policy evaluation separate from planner and simulator formulas
- keep review packet building separate from replay evaluation logic
- keep clients, normalization, scoring, services, and routes separated
- do not add route behavior by reimplementing engine logic in FastAPI
- do not hide rejected outputs unless a future contract explicitly allows filtering
- do not add trading, auth, UI, or broad persistence opportunistically
- update docs in the same change whenever commands, routes, or checkpoint behavior change

## Validation Contract

Minimum baseline check:

```bash
make validate
python -m polymarket_arb.cli scan --limit 5
python -m polymarket_arb.cli wallet-backfill --limit 10
python -m polymarket_arb.cli detect-copiers --limit 10
python -m polymarket_arb.cli paper-trade --limit 5
python -m polymarket_arb.cli review-packet --packet-type opportunities --limit 5
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/baseline.json --candidate-path /tmp/candidate.json
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1
python -m uvicorn polymarket_arb.api.main:app --reload
```

## Recommended Next Bounded Prompt

Phase 10D only:

- add bounded operator smoke-test discipline
- verify the runbook commands against fixture-backed flows
- verify checkpoint and `/health` inspection flow
- add no new routes
- add no new scoring logic
- add no live execution logic

If a future prompt asks for larger product changes, challenge scope first against this frozen baseline.
