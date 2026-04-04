# Architecture

## What Matters

The system is analytics-first and read-only in the early phases. It exists to turn public Polymarket data into evidence-backed operator workflows, not automated execution.

## Best Path

Keep the system monolithic and Python-first until real pressure justifies more complexity. Separate raw payload ingestion from normalization and downstream analytics so every later score can trace back to source evidence.

## Current Phase

Phase 1 implements only the scanner shell:

- Gamma event discovery
- CLOB book reads
- raw payload wrappers
- normalized event, market, and book models
- deterministic CLI output

## Target Layers

### Ingestion

- `clients/gamma.py`
- `clients/clob.py`
- `clients/data_api.py`
- `clients/ws_market.py`
- `models/raw.py`
- `models/normalized.py`

Rules:

- keep raw payloads separate from normalized records
- stamp normalized records with source ids and fetch timestamps
- avoid business logic inside API clients

### Opportunity Engine

Planned for later:

- discovery
- basket construction
- neg-risk analysis
- complement analysis
- fee model
- liquidity screen
- ranking and explanations

### Wallet Intelligence

Planned for later:

- wallet seed discovery
- wallet activity ingestion
- leg matching
- lead-lag scoring
- clustering
- confidence scoring

### Storage

Start local-first:

- DuckDB for analytical state
- Parquet for append-only snapshots
- small config files for deterministic execution

### Operator Surfaces

Phase order:

1. CLI
2. read-only FastAPI
3. thin dashboard if needed

## Risks / Tradeoffs

- Public APIs are inconsistent enough that normalization needs to be defensive.
- Live scan output cannot be time-stable, so only code paths and formatting should be deterministic.
- Premature wallet or execution work would create noise before the scanner is trustworthy.

## Validation

- unit tests for config and normalization
- CLI smoke run against live public endpoints
- strict lint and typecheck gates

