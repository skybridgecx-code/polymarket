# Roadmap

## Status

The repo is currently in Phase 8 with review-packet and replay evaluation added on top of the read-only baseline.

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

## Current

### Phase 8

Review packets and replay evaluation.

Deliverables:

- review packet models
- packet builder service
- replay evaluation service
- deterministic export format
- explicit pass/fail and drift reporting

## Recommended Next Phase

### Phase 9

Operator hardening and review workflow discipline.

Recommended scope:

- deployment and runtime documentation
- review workflow for packets and replay comparisons
- environment and observability hardening
- safer operator workflows around refresh cadence and checkpoint inspection
- packaging and release hygiene

Do not start live trading, auth, UI, or new model/scoring work in that phase.

## Later

Only after the frozen baseline is stable in real operator use should the repo consider execution research, and that work should remain explicitly isolated from the read-only analytics core.
