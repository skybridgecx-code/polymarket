# Codex Handoff

## Current Status

The repo is a shipped read-only Polymarket analytics and paper-trade research baseline with:

- read-only market and event ingestion
- fee-aware opportunity scanning
- wallet seed discovery and activity ingestion
- explainable lead/lag copier detection
- paper-trade execution plan generation and simulated fills
- post-simulation policy decisions on final paper-trade rows
- deterministic review packet generation and replay comparison
- read-only FastAPI operator API
- bounded real-time refresh orchestration with checkpointing
- operator runbook, examples, checklists, and failure-mode guidance

Not shipped:

- trading or order placement
- auth or private key work
- UI
- broad persistence or database work
- background workers
- execution automation
- live order submission

This frozen baseline does not add:

- Python behavior changes
- new routes
- new CLI commands
- scoring changes
- policy changes
- live trading behavior

## Operator Read Order

1. [README.md](/Users/muhammadaatif/polymarket-arb/README.md)
2. [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)
3. [docs/BASELINE.md](/Users/muhammadaatif/polymarket-arb/docs/BASELINE.md)
4. [ARCHITECTURE.md](/Users/muhammadaatif/polymarket-arb/ARCHITECTURE.md)
5. [CODEX_HANDOFF.md](/Users/muhammadaatif/polymarket-arb/CODEX_HANDOFF.md)

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

Use the runbook for exact checkpoint inspection, operator checklists, and failure-mode triage:

- [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)

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

## Recommended Next Step

Bounded operator validation discipline:

- verify the runbook commands against fixture-backed flows
- verify checkpoint and `/health` inspection flow
- add no new routes
- add no new scoring logic
- add no live execution logic

If a future prompt asks for larger product changes, challenge scope first against this frozen baseline.
