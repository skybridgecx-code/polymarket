# Roadmap

## Status

The repo is currently in Phase 9 with a deterministic paper-trade policy layer added on top of the existing paper-trade path.

## Completed

### Phase 1

Repo foundation and deterministic scanner shell.

Delivered:

- Python packaging and tooling
- typed config
- Gamma and CLOB clients
- raw and normalized market models
- deterministic `scan` CLI

### Phase 2

Fee-aware opportunity engine.

Delivered:

- binary complement analysis
- neg-risk basket analysis
- fee calculation
- liquidity screening
- ranked candidates with explanations and rejection reasons

### Phase 3

Wallet seed discovery and activity ingestion.

Delivered:

- leaderboard seed discovery
- top-holder seed discovery
- wallet activity fetcher
- normalized wallet seed and activity records
- deterministic `wallet-backfill` CLI output

### Phase 4

Lead/lag copier detection.

Delivered:

- same-leg same-side matching
- bounded lag-window matching
- repeated-event pair scoring
- confidence scoring
- evidence-backed accepted and rejected relationship reports

### Phase 5

Read-only operator API.

Delivered:

- FastAPI app entrypoint
- `GET /health`
- `GET /opportunities`
- `GET /wallets/backfill`
- `GET /relationships/copiers`

### Phase 6

Real-time refresh orchestration and checkpoint-safe state.

Delivered:

- market websocket consumer
- bounded refresh orchestration
- stale-state detection
- lightweight checkpoint file
- reconnect and resume handling

### Phase 7

Paper-trade execution research.

Delivered:

- execution plan model
- paper-trade simulation service
- explicit slippage model
- explicit kill-switch rules
- deterministic scenario fixtures and tests

### Phase 8

Review packets and replay evaluation.

Delivered:

- review packet models
- packet builder service
- replay evaluation service
- deterministic export format
- explicit pass/fail and drift reporting

## Current

### Phase 9

Paper-trade policy and guardrail layer, followed by docs alignment.

Deliverables:

- policy decision records with `allow` / `hold` / `deny`
- post-simulation policy evaluation
- recorded manual override fields
- recorded circuit-breaker state
- deterministic slippage-cap policy gate
- docs aligned to shipped policy behavior

## Recommended Next Phase

### Phase 10

Operator hardening and review workflow discipline.

Recommended scope:

- deployment and runtime documentation
- review workflow for packets and replay comparisons
- environment and observability hardening
- safer operator workflows around refresh cadence and checkpoint inspection
- packaging and release hygiene

Do not add live trading, auth, UI, or new model/scoring work in that phase.

## Later

Only after the frozen baseline is stable in real operator use should the repo consider execution research, and that work should remain explicitly isolated from the read-only analytics core.
