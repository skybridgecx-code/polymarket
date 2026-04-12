# Phase 18I — News Adapter Baseline

## Role
You are the implementation engine, not the architect.

Do not redesign the system.
Do not widen scope.
Do not touch unrelated modules.
Preserve current boundaries.

## Architectural truth
- `src/polymarket_arb/*` remains the bounded Polymarket intelligence/opportunity module.
- `src/future_system/theme_graph/*` is the canonical theme-linking layer.
- `src/future_system/evidence/*` is the canonical Polymarket evidence layer.
- `src/future_system/divergence/*` is the deterministic disagreement layer.
- `src/future_system/crypto_adapter/*` is the normalized crypto source boundary.
- `src/future_system/crypto_evidence/*` is the theme-linked crypto evidence layer.
- `src/future_system/comparison/*` is the deterministic Polymarket-vs-crypto comparison layer.
- `src/future_system/candidates/*` is the candidate signal layer.
- This phase adds the third evidence-family boundary: a bounded news adapter baseline.
- This phase is normalization and adapter-contract work only.
- Do not add live network fetches, scraping, schedulers, reasoning, policy, execution, UI, storage, or theme-linking logic.

## Why this phase exists
The system now understands:
- event markets
- crypto proxies
- cross-market comparison
- candidate surfacing

But it still cannot represent:
- headlines and articles as structured evidence inputs
- source trust / recency / contradiction-ready fields
- canonical news records for later theme linking

This phase creates the news-side contract, the same way 18E created the crypto-side contract.

## Phase objective
Build `src/future_system/news_adapter/` so the system can:

1. define canonical normalized news record models
2. define a small adapter protocol / interface
3. parse fixture-based raw news payloads into normalized records
4. filter normalized records by source / entity / recency inputs
5. emit deterministic normalized outputs with validation

This phase does not link news to themes yet.
This phase does not perform reasoning.
This phase does not fetch live data.

## In scope

Create these files if they do not already exist:

- `src/future_system/news_adapter/__init__.py`
- `src/future_system/news_adapter/models.py`
- `src/future_system/news_adapter/protocol.py`
- `src/future_system/news_adapter/parser.py`
- `src/future_system/news_adapter/filters.py`

Create tests:

- `tests/future_system/test_news_adapter_models.py`
- `tests/future_system/test_news_adapter_parser.py`
- `tests/future_system/test_news_adapter_filters.py`

Create fixtures:

- `tests/fixtures/future_system/news/raw_news_records.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- live HTTP/news clients
- scraping
- websocket/stream logic
- scheduler / polling jobs
- theme-linking / entity-linking beyond simple normalized record fields
- contradiction engine
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

### 1. `NormalizedNewsRecord`
Canonical normalized news/article/headline record.

Suggested fields:
- `source: Literal["fixture", "api", "feed"]`
- `publisher: str`
- `source_type: Literal["wire", "official", "newsroom", "analysis", "other"]`
- `article_id: str`
- `headline: str`
- `summary: str | None`
- `url: str | None`
- `published_at: datetime`
- `ingested_at: datetime | None`
- `entities: list[str]`
- `topics: list[str]`
- `trust_score: float`
- `language: str | None`
- `is_official_source: bool = False`

Validation:
- `publisher`, `article_id`, `headline` must be non-empty
- `trust_score` must be within `[0.0, 1.0]`
- `entities` and `topics` must be normalized string lists
- `url` may be optional
- `published_at` is required

### 2. `NewsAdapterParseResult`
Represents parser output.

Suggested fields:
- `publisher_count: int`
- `records: list[NormalizedNewsRecord]`
- `skipped_records: int`
- `flags: list[str]`

### 3. `NewsRecordFilter`
Optional helper model if useful.

### 4. `NewsAdapterError`
Raised when raw payloads cannot be parsed into valid normalized news records.

## Adapter protocol

Implement a very small protocol or interface in `protocol.py`.

It should define a bounded contract for adapter-like behavior, such as:
- parse raw payloads into normalized records
- optionally filter normalized records by simple criteria

Do not add live client methods.
Do not add auth.
Do not add retries.

This is a contract layer only.

## Parser behavior

Implement deterministic parsing from fixture-based raw payloads.

Assume fixtures contain a list of raw records representing a small mixed publisher snapshot set.

Parser rules:

1. Accept either:
- already-loaded Python mappings / sequences
- or JSON fixture content loaded by tests

2. Map raw fields deterministically into `NormalizedNewsRecord`

3. Normalize entities/topics:
- trim whitespace
- de-duplicate case-insensitively
- preserve deterministic output order
- discard empty strings

4. Skip malformed records only when they are clearly unusable.
- count them in `skipped_records`
- add an explicit flag like `skipped_invalid_records`
- do not silently swallow payload-format failures that should break the parse

5. Support a mix of source types in the fixture:
- wire
- official
- newsroom
- analysis

6. Keep trust-score handling deterministic:
- if fixture already provides trust_score, validate and use it
- do not invent complex scoring logic here

7. Normalize publisher/article/headline fields consistently.
No fuzzy correction.

## Filter behavior

Implement deterministic filtering helpers.

Suggested supported filters:
- by exact publisher
- by entity presence
- by topic presence
- by `is_official_source`
- by minimum `published_at` cutoff

Rules:
- exact normalized match only for publisher/entity/topic
- preserve input order after filtering
- return empty list when nothing matches
- no fuzzy matching

## Test requirements

### `test_news_adapter_models.py`
Cover:
- valid normalized record
- invalid trust score rejected
- required string fields enforced
- entity/topic normalization enforced

### `test_news_adapter_parser.py`
Cover:
- valid fixture parses into normalized records
- malformed records increase `skipped_records`
- multiple source types supported
- parser flags deterministic
- entity/topic normalization deterministic

### `test_news_adapter_filters.py`
Cover:
- publisher filter works
- entity filter works
- topic filter works
- official-source filter works
- published_at cutoff works
- unmatched filters return empty list
- input order preserved

## Fixtures
Create a small deterministic fixture set with at least:
- one wire article
- one official-source article or release
- one newsroom article
- one analysis article
- one malformed record that should be skipped

Each should include enough fields to exercise parser and filter behavior.

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement theme-linking or reasoning in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/news_adapter/*` exists with the files listed above
2. typed models validate correctly
3. parser emits deterministic normalized news records
4. malformed fixture records are handled deterministically
5. filters work deterministically
6. tests pass
7. no unrelated modules were modified
8. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new news adapter module if mypy is already in use

At minimum, run:
- targeted pytest for the new news adapter tests
- narrow ruff check for touched files
- narrow mypy check for the new news adapter module

## Final output format
Return only:
1. concise summary
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. any deviations from spec
6. explicit note whether `src/polymarket_arb/*` was untouched

List only the final successful validation commands once in section 3.
Mention earlier failed runs only in section 4 if they occurred.

Do not widen the phase.
Do not start theme-linking for news.
Do not start reasoning or policy.
Complete only this bounded phase.
