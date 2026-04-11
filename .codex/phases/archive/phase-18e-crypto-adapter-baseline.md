# Phase 18E — Crypto Adapter Baseline

## Role
You are the implementation engine, not the architect.

Do not redesign the system.
Do not widen scope.
Do not touch unrelated modules.
Preserve current boundaries.

## Architectural truth
- `src/polymarket_arb/*` remains the bounded Polymarket intelligence/opportunity module.
- `src/future_system/theme_graph/*` is the canonical theme-linking layer.
- `src/future_system/evidence/*` is the canonical evidence contract + assembly layer.
- `src/future_system/divergence/*` is the deterministic disagreement layer.
- This phase adds the first non-Polymarket source boundary: a bounded crypto adapter baseline.
- This phase is normalization and adapter-contract work only.
- Do not add live network fetches, websocket streams, schedulers, policy logic, reasoning, UI, persistence, or execution.

## Why this phase exists
The larger system now has internal structure but still only knows how to operate on Polymarket-shaped inputs.

Before it can compare markets, it needs a clean external-source adapter boundary that:
- accepts raw source payloads
- normalizes them into canonical crypto market-state models
- exposes deterministic adapter behavior
- stays small and inspectable

This phase proves that boundary with fixture-based parsing only.

## Phase objective
Build `src/future_system/crypto_adapter/` so the system can:

1. define canonical normalized crypto market-state models
2. define a small adapter protocol / interface
3. parse fixture-based raw payloads into normalized crypto market states
4. filter to only relevant symbols from manual inputs
5. emit deterministic normalized outputs with validation

This phase does not compare crypto to Polymarket yet.
It does not assemble mixed-source evidence yet.
It does not fetch live data.

## In scope

Create these files if they do not already exist:

- `src/future_system/crypto_adapter/__init__.py`
- `src/future_system/crypto_adapter/models.py`
- `src/future_system/crypto_adapter/protocol.py`
- `src/future_system/crypto_adapter/parser.py`
- `src/future_system/crypto_adapter/filters.py`

Create tests:

- `tests/future_system/test_crypto_adapter_models.py`
- `tests/future_system/test_crypto_adapter_parser.py`
- `tests/future_system/test_crypto_adapter_filters.py`

Create fixtures:

- `tests/fixtures/future_system/crypto/market_snapshots.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- live HTTP clients
- websocket clients
- scheduler / polling jobs
- cross-market evidence merger
- divergence updates for crypto
- news adapters
- reasoning / prompts / LLM logic
- policy engine
- execution logic
- CLI/API surfaces
- dashboard/UI
- persistence/database
- repo-wide refactors

## Do not touch
- `src/polymarket_arb/*`
- trade service / live order code
- existing CLI behavior
- unrelated phase docs

If imports require tiny changes elsewhere, keep them minimal and explain them.

## Required models

Implement strongly typed models using existing repo conventions.

### 1. `NormalizedCryptoMarketState`
Canonical normalized crypto market snapshot.

Suggested fields:
- `source: Literal["fixture", "exchange"]`
- `exchange: str`
- `symbol: str`
- `base_asset: str`
- `quote_asset: str`
- `market_type: Literal["spot", "perp"]`
- `last_price: float | None`
- `bid_price: float | None`
- `ask_price: float | None`
- `mid_price: float | None`
- `volume_24h: float | None`
- `open_interest: float | None`
- `funding_rate: float | None`
- `snapshot_at: datetime`
- `status: Literal["active", "halted", "unknown"]`

Validation:
- `symbol`, `base_asset`, `quote_asset`, `exchange` must be non-empty
- numeric price/volume/open_interest fields cannot be negative
- `funding_rate` may be negative but must be bounded reasonably if you choose validation
- if both `bid_price` and `ask_price` are present, `ask_price >= bid_price`
- if `mid_price` is missing and both bid/ask exist, parser should compute it deterministically

### 2. `CryptoAdapterParseResult`
Represents parser output.

Suggested fields:
- `exchange: str`
- `market_states: list[NormalizedCryptoMarketState]`
- `skipped_records: int`
- `flags: list[str]`

### 3. `CryptoSymbolFilter`
Optional helper model if useful.

### 4. `CryptoAdapterError`
Raised when raw payloads cannot be parsed into valid normalized states.

## Adapter protocol

Implement a very small protocol or interface in `protocol.py`.

It should define a bounded contract for adapter-like behavior, such as:
- parse raw payloads into normalized states
- optionally filter normalized states by allowed symbols

Do not add live client methods.
Do not add auth.
Do not add retries.

This is a contract layer only.

## Parser behavior

Implement deterministic parsing from fixture-based raw payloads.

Assume fixtures contain a list of raw records representing a small exchange-style snapshot set.

Parser rules:

1. Accept either:
- already-loaded Python mappings / sequences
- or JSON fixture content loaded by tests

2. Map raw fields deterministically into `NormalizedCryptoMarketState`

3. Compute `mid_price`:
- if raw mid exists, use it
- else if bid and ask both exist, use `(bid + ask) / 2`
- else leave `None`

4. Skip malformed records only when they are clearly unusable.
- count them in `skipped_records`
- add an explicit flag like `skipped_invalid_records`
- do not silently swallow parser problems that break the whole payload format

5. Support both `spot` and `perp` records in the fixture

6. Keep symbol normalization deterministic.
Suggested examples:
- `BTC-USD`
- `ETH-USD`
- `BTC-PERP`

Do not invent complex symbol translation logic.

## Filter behavior

Implement deterministic filtering helpers.

Suggested behavior:
- include only explicitly requested symbols when a filter list is provided
- preserve input order after filtering
- exact normalized symbol match only
- return empty list when nothing matches

No fuzzy matching.

## Test requirements

### `test_crypto_adapter_models.py`
Cover:
- valid normalized state
- negative numeric fields rejected
- bid/ask ordering enforced
- required string fields enforced

### `test_crypto_adapter_parser.py`
Cover:
- valid fixture parses into normalized states
- mid price computed deterministically from bid/ask when missing
- malformed records increase `skipped_records`
- spot and perp records both supported
- parser flags deterministic

### `test_crypto_adapter_filters.py`
Cover:
- exact symbol filter works
- unmatched symbols return empty list
- input order preserved
- normalization behavior deterministic

## Fixtures
Create a small deterministic fixture set with at least:
- one BTC spot record
- one ETH spot record
- one BTC perp record
- one malformed record that should be skipped

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement cross-market comparison in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/crypto_adapter/*` exists with the files listed above
2. typed models validate correctly
3. parser emits deterministic normalized crypto market states
4. malformed fixture records are handled deterministically
5. symbol filtering works deterministically
6. tests pass
7. no unrelated modules were modified
8. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new crypto adapter module if mypy is already in use

At minimum, run:
- targeted pytest for the new crypto adapter tests
- narrow ruff check for touched files
- narrow mypy check for the new crypto adapter module

## Final output format
Return only:
1. concise summary
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. any deviations from spec
6. explicit note whether `src/polymarket_arb/*` was untouched

Do not widen the phase.
Do not start live exchange ingestion.
Do not start mixed-source evidence merging.
Do not start reasoning or policy.
Complete only this bounded phase.
