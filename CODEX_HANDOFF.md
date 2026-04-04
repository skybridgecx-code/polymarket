# Codex Handoff

## Current Status

The repo now includes a Phase 7B paper-trade execution research layer on top of the read-only baseline.

Shipped and in scope:

- read-only market and event ingestion
- fee-aware opportunity scanning
- wallet seed discovery and activity ingestion
- explainable lead/lag copier detection
- paper-trade execution plan generation and simulated fills
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

## Read First

- [README.md](/Users/muhammadaatif/polymarket-arb/README.md)
- [ARCHITECTURE.md](/Users/muhammadaatif/polymarket-arb/ARCHITECTURE.md)
- [ROADMAP.md](/Users/muhammadaatif/polymarket-arb/ROADMAP.md)
- [docs/BASELINE.md](/Users/muhammadaatif/polymarket-arb/docs/BASELINE.md)

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

## Guardrails For Future Phases

- stay read-only unless a future phase explicitly changes that boundary
- keep paper-trade simulation separate from any future live-capable code path
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
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1
python -m uvicorn polymarket_arb.api.main:app --reload
```

## Recommended Next Bounded Prompt

Phase 7C only:

- improve operator hardening and release discipline
- document review workflow for paper-trade plans
- document deployment, runtime env, and checkpoint inspection flows
- add no new scoring logic
- add no new routes
- add no live execution logic

If a future prompt asks for larger product changes, challenge scope first against this frozen baseline.
