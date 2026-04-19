# Roadmap

## Status

The repo is currently in Phase 36D with bounded local operator packaging manual-smoke and documentation reconciliation work.

The Phase 11 baseline is still the core `polymarket_arb` runtime foundation; later phases added `future_system` local operator UI workflow, demo-launcher reliability hardening, and local review outcome packaging.

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

### Phase 9

Paper-trade policy and guardrail layer.

Delivered:

- policy decision records with `allow` / `hold` / `deny`
- post-simulation policy evaluation
- recorded manual override fields
- recorded circuit-breaker state
- deterministic slippage-cap policy gate

### Phase 10A

Operator runbook and checkpoint inspection hardening.

Delivered:

- operator runbook for `orchestrate-refresh`, `paper-trade`, `review-packet`, and `replay-evaluate`
- checkpoint inspection workflow documentation
- `idle` / `ok` / `stale` health interpretation grounded in current checkpoint fields
- runtime and environment documentation grounded in current config

### Phase 10B

Operator workflow examples and review packet discipline.

Delivered:

- concrete example flows for bounded refresh/checkpoint/health inspection
- concrete example flow for `paper-trade` plus `review-packet`
- concrete example flow for `replay-evaluate`
- command-selection guidance for the shipped operator commands
- tighter review and replay discipline guidance

### Phase 10C

Operator checklist and failure-mode quick reference.

Delivered:

- pre-run checklist for the shipped operator commands
- post-run checklist for checkpoint, health, packet, and replay inspection
- failure-mode quick reference for current stale reasons and websocket no-message exit behavior
- concise operator triage flow

### Phase 10D

Final baseline freeze and release/handoff polish.

Delivered:

- final docs consistency sweep across the shipped baseline docs
- one clear current shipped-system summary
- one clear operator entrypoint and read order
- one clear in-scope vs not-in-scope statement
- one concise recommended next step after the frozen baseline
- removal of stale wording and duplicate phase-thread guidance

## Current

### Phase 36D

CLI packaging manual smoke and repo-status reconciliation.

Deliverables:

- docs-only manual smoke path for CLI packaging entrypoint
- explicit end-to-end operator sequence:
  validate -> prepare -> launch/review -> save local decision -> package -> cleanup
- roadmap/handoff/release-index/runbook status reconciliation to current shipped state
- no runtime behavior changes

## Recommended Next Step

After Phase 36D docs/manual-smoke reconciliation, the next step should be Phase 36E closeout:

- track closeout for CLI packaging entrypoint
- capture final validation baseline and known warnings
- keep no-live-execution/no-auth/no-db-queue boundaries intact

## Later

Only after the frozen baseline is stable in real operator use should the repo consider execution research, and that work should remain explicitly isolated from the read-only analytics core.
