# Phase 18C — Evidence Packet Contracts + Polymarket Evidence Assembler

## Role
You are the implementation engine, not the architect.

Do not redesign the system.
Do not widen scope.
Do not touch unrelated modules.
Preserve current boundaries.

## Architectural truth
- `src/polymarket_arb/*` remains the bounded Polymarket intelligence/opportunity module.
- `src/future_system/theme_graph/*` is now the canonical theme-linking layer.
- This phase builds the next bridge: a canonical evidence contract layer plus the first assembler for linked Polymarket evidence.
- Do not add crypto, macro, news, LLM, policy, execution, UI, storage, or network fetch logic in this phase.

## Why this phase exists
The larger system needs one canonical evidence shape before adding more source adapters.

Without a hard evidence packet contract:
- crypto will invent one shape
- news will invent another
- divergence logic will become messy
- reasoning/policy layers will drift

This phase creates the contract and proves it with Polymarket-linked evidence only.

## Phase objective
Build `src/future_system/evidence/` so the system can:

1. accept a `ThemeLinkPacket`
2. accept one or more normalized Polymarket market-state objects
3. deterministically select only the linked markets
4. compute bounded freshness and liquidity summaries
5. emit a canonical `ThemeEvidencePacket`

This phase is structure plus deterministic assembly only.
No external data collection.
No divergence logic.
No AI reasoning.

## In scope

Create these files if they do not already exist:

- `src/future_system/evidence/__init__.py`
- `src/future_system/evidence/models.py`
- `src/future_system/evidence/assembler.py`
- `src/future_system/evidence/freshness.py`
- `src/future_system/evidence/scoring.py`

Create tests:

- `tests/future_system/test_evidence_models.py`
- `tests/future_system/test_evidence_assembler.py`
- `tests/future_system/test_evidence_scoring.py`

Create fixtures:

- `tests/fixtures/future_system/evidence/polymarket_market_states.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- crypto adapters
- macro adapters
- news adapters
- divergence engine
- reasoning / prompts / LLM logic
- policy engine
- execution logic
- CLI/API surfaces
- dashboard/UI
- persistence/database
- background jobs
- live network calls
- repo-wide refactors

## Do not touch
- `src/polymarket_arb/*`
- trade service / live order code
- existing CLI behavior
- unrelated phase docs

If imports require tiny changes elsewhere, keep them minimal and explain them.

## Required models

Implement strongly typed models using existing repo conventions.

### 1. `NormalizedPolymarketMarketState`
A bounded normalized snapshot input model for evidence assembly.

Suggested fields:
- `market_slug: str | None`
- `event_slug: str | None`
- `condition_id: str | None`
- `question: str | None`
- `yes_bid: float | None`
- `yes_ask: float | None`
- `no_bid: float | None`
- `no_ask: float | None`
- `last_price_yes: float | None`
- `volume_24h: float | None`
- `depth_near_mid: float | None`
- `snapshot_at: datetime`
- `last_trade_at: datetime | None`
- `resolution_at: datetime | None`
- `status: Literal["active", "closed", "resolved", "unknown"]`

Validation:
- all probability-like values must be within `[0.0, 1.0]`
- volume/depth cannot be negative
- require at least one identifier among `condition_id`, `market_slug`, `event_slug`

### 2. `PolymarketMarketEvidence`
Represents one matched market’s evidence summary.

Suggested fields:
- `market_slug: str | None`
- `condition_id: str | None`
- `implied_yes_probability: float | None`
- `spread: float | None`
- `liquidity_score: float`
- `freshness_score: float`
- `flags: list[str]`
- `is_primary: bool = False`

### 3. `ThemeEvidencePacket`
Canonical evidence output for one theme.

Suggested fields:
- `theme_id: str`
- `primary_market_slug: str | None`
- `market_evidence: list[PolymarketMarketEvidence]`
- `aggregate_yes_probability: float | None`
- `liquidity_score: float`
- `freshness_score: float`
- `evidence_score: float`
- `flags: list[str]`
- `explanation: str`

### 4. `EvidenceAssemblyError`
Raised when assembly cannot build a valid packet from the provided linked inputs.

## Assembly behavior

Implement deterministic assembly from:

- `ThemeLinkPacket`
- sequence of `NormalizedPolymarketMarketState` or plain mappings that validate into that model

Rules:

1. Only include market states that match the theme packet’s linked markets by:
   - exact `condition_id` first
   - then exact `market_slug`
   - then exact `event_slug`

2. If no provided market states match the theme packet’s linked markets:
   - raise `EvidenceAssemblyError`
   - do not invent a packet

3. Compute implied probability:
   - prefer `last_price_yes`
   - else use midpoint from `yes_bid` and `yes_ask` when both exist
   - else leave as `None` and add a flag

4. Compute spread:
   - use `yes_ask - yes_bid` when both exist
   - else `None` and add a flag

5. Compute freshness score deterministically from `snapshot_at` age relative to an explicit `reference_time` input.
   - no hidden use of current system time inside core scoring functions
   - keep scoring simple and explicit

Suggested buckets:
- <= 5 minutes: 1.00
- <= 30 minutes: 0.80
- <= 2 hours: 0.50
- > 2 hours: 0.20 and add stale flag

6. Compute liquidity score deterministically from bounded spread/depth/volume inputs.
   Keep this simple and explainable.
   Do not over-engineer a fake quant model.

7. Select primary market deterministically:
   - exact `condition_id` match wins if available among matched records
   - otherwise highest liquidity score wins
   - ties break by `market_slug` ascending

8. Compute aggregate probability:
   - weighted average of matched market implied probabilities
   - weights should be based on liquidity score
   - ignore markets with `None` implied probability
   - if none have implied probability, aggregate is `None`

9. Compute packet-level scores:
   - packet liquidity score = mean of market liquidity scores
   - packet freshness score = mean of market freshness scores
   - evidence score = deterministic combination of liquidity + freshness
   - keep all scores within `[0.0, 1.0]`

10. Surface explicit flags for:
   - stale snapshot
   - missing book data
   - missing implied probability
   - matched market missing identifiers where relevant
   - no aggregate probability available

## Scoring requirements
Create small pure functions in `freshness.py` and `scoring.py`.

Keep them:
- deterministic
- bounded
- easy to inspect
- free of side effects

No randomization.
No hidden global time.
No network assumptions.

## Test requirements

### `test_evidence_models.py`
Cover:
- valid market state model
- invalid negative volume/depth rejected
- invalid probabilities outside `[0,1]` rejected
- identifier requirement enforced

### `test_evidence_assembler.py`
Cover:
- linked market matched by `condition_id`
- linked market matched by `market_slug`
- unlinked market excluded
- no matches raises `EvidenceAssemblyError`
- primary market selection deterministic
- aggregate probability calculation deterministic
- stale flag emitted when appropriate
- missing book data flag emitted when appropriate

### `test_evidence_scoring.py`
Cover:
- freshness score buckets
- liquidity score bounded in `[0,1]`
- evidence score bounded in `[0,1]`
- deterministic outputs for known inputs

## Fixtures
Create a small deterministic fixture set with at least:
- one clearly linked liquid market
- one linked but weaker/staler market
- one unrelated market that must be ignored

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- no future-phase “helpers” beyond what this phase needs

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/evidence/*` exists with the files listed above
2. typed models validate correctly
3. assembler consumes `ThemeLinkPacket` + normalized market states
4. only linked markets are included
5. deterministic primary market selection works
6. deterministic aggregate probability works
7. stale/missing-data flags surface correctly
8. tests pass
9. no unrelated modules were modified
10. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow lint/type checks for touched files if repo norms require them

At minimum, run:
- targeted pytest for the new evidence module tests
- narrow ruff check for touched files
- narrow mypy check for the new evidence module if mypy is already in use

## Final output format
Return only:
1. concise summary
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. any deviations from spec
6. explicit note whether `src/polymarket_arb/*` was untouched

Do not widen the phase.
Do not start crypto ingestion.
Do not start divergence logic.
Complete only this bounded phase.
