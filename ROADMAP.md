# Roadmap

## Phase 1

Repo foundation and deterministic scanner shell.

Deliverables:

- Python packaging and tooling
- typed config
- Gamma events client
- CLOB books client
- normalized event, market, and book models
- `scan` CLI
- fixtures and unit tests

## Phase 2

Fee-aware opportunity engine.

Deliverables:

- neg-risk analyzer
- complement analyzer
- fee model
- liquidity screen
- explanations and rejection reasons

## Phase 3

Wallet seed discovery and activity ingestion.

Deliverables:

- leaderboard seeds
- top holder import
- activity fetcher
- normalized wallet activity
- DuckDB and Parquet persistence

## Phase 4

Lead-lag copier detection.

Deliverables:

- same-leg matcher
- lag window scoring
- repeated-event confidence logic
- relationship reports with evidence

## Phase 5

Read-only API and operator reports.

Deliverables:

- FastAPI routes
- health endpoint
- latest opportunity and wallet evidence routes

## Phase 6

Real-time stream and refresh orchestration.

Deliverables:

- market WebSocket consumer
- refresh scheduler
- stale-state detection
- restart-safe checkpoints

## Phase 7

Execution research only.

Deliverables:

- paper-trade simulation
- explicit execution risk documentation
- hard isolation from analytics core

