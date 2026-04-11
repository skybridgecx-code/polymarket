# Phase 18D — Deterministic Divergence Contracts + Disagreement Detector

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
- This phase adds the next deterministic bridge: divergence contracts and a disagreement detector over canonical evidence packets.
- This phase is still Polymarket-evidence-only.
- Do not add crypto, macro, news, LLM, policy, execution, UI, storage, or network fetch logic.

## Why this phase exists
Before adding more data sources, the system needs a clean way to answer:

- is the linked evidence internally aligned or internally conflicted
- is the implied probability coherent across linked market evidence
- is the packet actionable, weak, stale, or too ambiguous

Without this layer, future cross-market comparison will be sloppy because there is no canonical disagreement model yet.

## Phase objective
Build `src/future_system/divergence/` so the system can:

1. accept a `ThemeEvidencePacket`
2. measure probability disagreement across linked market evidence
3. measure evidence quality weakness from liquidity/freshness/flags
4. classify posture deterministically:
   - `aligned`
   - `mixed`
   - `conflicted`
   - `insufficient`
5. emit a canonical `ThemeDivergencePacket`

This phase is deterministic analysis only.
No external fetches.
No AI reasoning.
No decisions/policy engine.

## In scope

Create these files if they do not already exist:

- `src/future_system/divergence/__init__.py`
- `src/future_system/divergence/models.py`
- `src/future_system/divergence/detector.py`
- `src/future_system/divergence/scoring.py`

Create tests:

- `tests/future_system/test_divergence_models.py`
- `tests/future_system/test_divergence_detector.py`
- `tests/future_system/test_divergence_scoring.py`

Create fixtures:

- `tests/fixtures/future_system/divergence/theme_evidence_packets.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- crypto adapters
- macro adapters
- news adapters
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

### 1. `DivergenceInputSummary`
Optional internal helper model if useful, otherwise skip.

### 2. `MarketDisagreement`
Represents one market evidence item’s disagreement contribution.

Suggested fields:
- `market_slug: str | None`
- `condition_id: str | None`
- `implied_yes_probability: float | None`
- `distance_from_aggregate: float | None`
- `liquidity_score: float`
- `freshness_score: float`
- `flags: list[str]`
- `severity: Literal["low", "medium", "high", "unknown"]`

### 3. `ThemeDivergencePacket`
Canonical divergence output for one theme.

Suggested fields:
- `theme_id: str`
- `primary_market_slug: str | None`
- `aggregate_yes_probability: float | None`
- `dispersion_score: float`
- `quality_penalty: float`
- `divergence_score: float`
- `posture: Literal["aligned", "mixed", "conflicted", "insufficient"]`
- `market_disagreements: list[MarketDisagreement]`
- `flags: list[str]`
- `explanation: str`

### 4. `DivergenceDetectionError`
Raised when divergence cannot be computed from the provided evidence packet.

## Detection behavior

Implement deterministic detection from a `ThemeEvidencePacket`.

Rules:

1. Require at least one `market_evidence` entry.
   - otherwise raise `DivergenceDetectionError`

2. If `aggregate_yes_probability` is `None`:
   - do not invent one
   - posture should become `insufficient`
   - add explicit flag like `no_aggregate_probability`

3. For each market evidence item:
   - if `implied_yes_probability` is `None`, keep disagreement contribution as unknown
   - otherwise compute absolute distance from `aggregate_yes_probability`

4. Dispersion score:
   - deterministic bounded score in `[0.0, 1.0]`
   - should increase as linked markets disagree more on implied probability
   - should not be a fake quant model
   - simple, explicit, inspectable

Suggested basis:
- mean absolute distance from aggregate across markets with probabilities
- optionally give slight extra weight to low-liquidity/high-flag inconsistency, but keep simple

5. Quality penalty:
   - deterministic bounded penalty in `[0.0, 1.0]`
   - should increase when:
     - packet liquidity is weak
     - packet freshness is weak
     - packet flags show stale/missing-data issues
   - keep simple and explicit

6. Divergence score:
   - deterministic bounded score in `[0.0, 1.0]`
   - combine dispersion score and quality penalty
   - should represent “degree of disagreement / non-cleanliness”
   - higher means less internally coherent / less clean

7. Posture classification:
   - `aligned`
     - low dispersion
     - acceptable evidence quality
   - `mixed`
     - moderate dispersion or moderate quality weakness
   - `conflicted`
     - high dispersion
   - `insufficient`
     - aggregate probability missing
     - or too little usable probability evidence
     - or evidence packet is dominated by missing data

Use deterministic thresholds and keep them explicit in code.

8. Flags:
   Surface explicit packet-level flags for cases like:
   - `no_aggregate_probability`
   - `single_usable_market`
   - `stale_evidence`
   - `weak_liquidity`
   - `missing_probability_inputs`
   - `high_internal_dispersion`

9. Explanation:
   Produce a short deterministic explanation string summarizing:
   - aggregate probability state
   - number of usable markets
   - divergence posture
   - key flags

## Scoring requirements
Create small pure functions in `scoring.py`.

Keep them:
- deterministic
- bounded
- easy to inspect
- free of side effects

No randomization.
No hidden global time.
No network assumptions.

Suggested functions:
- `compute_dispersion_score(...)`
- `compute_quality_penalty(...)`
- `compute_divergence_score(...)`
- `classify_divergence_posture(...)`
- `classify_market_disagreement_severity(...)`

## Test requirements

### `test_divergence_models.py`
Cover:
- valid packet models
- invalid bounded scores rejected
- invalid posture/severity rejected

### `test_divergence_detector.py`
Cover:
- aligned packet produces `aligned`
- moderate disagreement produces `mixed`
- high disagreement produces `conflicted`
- missing aggregate produces `insufficient`
- single usable market produces `insufficient` or explicit weak flag per your threshold design
- market disagreement entries are deterministic
- explanation string is deterministic
- explicit flags surface correctly

### `test_divergence_scoring.py`
Cover:
- dispersion score bounded in `[0,1]`
- quality penalty bounded in `[0,1]`
- divergence score bounded in `[0,1]`
- posture thresholds deterministic for known inputs

## Fixtures
Create a small deterministic fixture set with at least:
- one aligned packet
- one mixed packet
- one conflicted packet
- one insufficient packet

These can be JSON representations of canonical `ThemeEvidencePacket`-shaped inputs.

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement future cross-market adapters here

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/divergence/*` exists with the files listed above
2. typed models validate correctly
3. detector consumes `ThemeEvidencePacket`
4. divergence score is deterministic and bounded
5. posture classification works for aligned / mixed / conflicted / insufficient
6. explicit flags surface correctly
7. tests pass
8. no unrelated modules were modified
9. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new divergence module if mypy is already in use

At minimum, run:
- targeted pytest for the new divergence module tests
- narrow ruff check for touched files
- narrow mypy check for the new divergence module

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
Do not start news ingestion.
Do not start reasoning or policy.
Complete only this bounded phase.
