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
- operator runbook, examples, checklists, failure-mode guidance, and validation guide
- shipped local `future_system` operator UI workflow for local artifact review/edit
- shipped local review outcome packaging flow with CLI entrypoint
- docs-locked execution boundary contract for handing approved packages to `cryp` execution review surfaces

Not shipped:

- trading or order placement
- auth or private key work
- production-facing UI for `polymarket_arb` core
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

Operator validation guide:

- [docs/OPERATOR_VALIDATION.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_VALIDATION.md)

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

Future system local operator workflow:

```bash
make future-system-operator-ui-demo-validate
make future-system-operator-ui-demo-prepare
make future-system-operator-ui-demo
python -m future_system.cli.review_outcome_package \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs \
  --target-root .tmp/future-system-operator-ui-demo/packages
make future-system-operator-ui-demo-clean
```

Packaging track closeout reference:
- [docs/PHASE_36E_CLI_PACKAGING_TRACK_CLOSEOUT.md](/Users/muhammadaatif/polymarket-arb/docs/PHASE_36E_CLI_PACKAGING_TRACK_CLOSEOUT.md)

Execution boundary contract reference:
- [docs/PHASE_37A_EXECUTION_BOUNDARY_CONTRACT.md](/Users/muhammadaatif/polymarket-arb/docs/PHASE_37A_EXECUTION_BOUNDARY_CONTRACT.md)

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

Use the validation guide for exact repeatable operator checks:

- [docs/OPERATOR_VALIDATION.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_VALIDATION.md)

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

Phase 37A execution boundary contract is now defined:

- shipped local operator path is:
  validate -> prepare -> launch/review -> save local decision -> package -> cleanup
- packaged handoff boundary to `cryp` is docs-locked; no runtime coupling was added
- keep local artifact-file boundaries intact
- open the next phase only for explicit contract implementation work (for example schema validators or bounded intake/export wiring)

If a future prompt asks for larger product changes, challenge scope first against this frozen baseline.
