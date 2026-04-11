# Phase 18G — Polymarket vs Crypto Comparison

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
- This phase adds the first cross-market comparison layer between canonical Polymarket evidence and canonical crypto evidence.
- This phase is deterministic comparison only.
- Do not add news, reasoning, policy, execution, UI, storage, or live network logic.

## Why this phase exists
The system now has two separate theme-scoped evidence families:
- Polymarket evidence
- crypto proxy evidence

But it still cannot answer:
- are they directionally aligned
- are they weakly aligned
- are they conflicting
- is crypto missing or insufficient
- how strong is the comparison signal

This phase creates the first canonical cross-market comparison packet.

## Phase objective
Build `src/future_system/comparison/` so the system can:

1. accept a `ThemeEvidencePacket`
2. accept a `ThemeCryptoEvidencePacket`
3. compare them deterministically for one theme
4. classify posture:
   - `aligned`
   - `weakly_aligned`
   - `conflicted`
   - `insufficient`
5. emit a canonical `ThemeComparisonPacket`

This phase does not do LLM reasoning.
This phase does not make policy decisions.
This phase does not execute trades.

## In scope

Create these files if they do not already exist:

- `src/future_system/comparison/__init__.py`
- `src/future_system/comparison/models.py`
- `src/future_system/comparison/comparator.py`
- `src/future_system/comparison/scoring.py`

Create tests:

- `tests/future_system/test_comparison_models.py`
- `tests/future_system/test_comparison_comparator.py`
- `tests/future_system/test_comparison_scoring.py`

Create fixtures:

- `tests/fixtures/future_system/comparison/theme_comparison_inputs.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- news adapters
- reasoning / prompts / LLM logic
- policy engine
- execution logic
- CLI/API surfaces
- dashboard/UI
- persistence/database
- schedulers
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

### 1. `ComparisonDirection`
Use an enum or literal model for:
- `bullish`
- `bearish`
- `mixed`
- `unknown`

This represents the comparison-implied directional posture of each evidence family.

### 2. `ComparisonAlignment`
Use an enum or literal model for:
- `aligned`
- `weakly_aligned`
- `conflicted`
- `insufficient`

### 3. `EvidenceFamilySummary`
Represents a normalized summary of one evidence family for comparison.

Suggested fields:
- `family: Literal["polymarket", "crypto"]`
- `direction: ComparisonDirection`
- `strength_score: float`
- `freshness_score: float`
- `liquidity_score: float | None`
- `coverage_score: float | None`
- `flags: list[str]`

### 4. `ThemeComparisonPacket`
Canonical comparison output for one theme.

Suggested fields:
- `theme_id: str`
- `polymarket_summary: EvidenceFamilySummary`
- `crypto_summary: EvidenceFamilySummary`
- `alignment: ComparisonAlignment`
- `agreement_score: float`
- `confidence_score: float`
- `flags: list[str]`
- `explanation: str`

### 5. `ComparisonError`
Raised when comparison cannot be computed from the provided packets.

## Comparison behavior

Implement deterministic comparison from:
- `ThemeEvidencePacket`
- `ThemeCryptoEvidencePacket`

Rules:

1. Theme ids must match.
   - if they do not, raise `ComparisonError`

2. Derive Polymarket direction deterministically from `aggregate_yes_probability`:
   Suggested thresholds:
   - `> 0.55` -> `bullish`
   - `< 0.45` -> `bearish`
   - otherwise `mixed`
   - if aggregate missing -> `unknown`

Keep thresholds explicit in code.

3. Derive crypto direction deterministically from theme-linked proxy evidence.

Use a simple explicit approach:
- evaluate each proxy using its `direction_if_theme_up`
- infer whether observed crypto state is supportive, unsupportive, mixed, or unknown
- keep this small and inspectable

Suggested interpretation:
- for proxies with `direction_if_theme_up == "up"`:
  - presence of usable price evidence counts as supportive-positive input
- for proxies with `direction_if_theme_up == "down"`:
  - usable price evidence counts as inverse-support input
- if proxy evidence is too incomplete, it contributes `unknown`

You must choose a clear deterministic rule and apply it consistently in code/tests.
Do not invent a fake market-return model.
This is a bounded structural comparison phase, not full signal inference.

A practical simple rule is acceptable, for example:
- if majority of usable proxies are role-weighted supportive of theme-up -> `bullish`
- if majority are role-weighted supportive of theme-down -> `bearish`
- ties / mixed -> `mixed`
- too few usable proxies -> `unknown`

4. Strength score:
- derive bounded family-level strength scores in `[0.0, 1.0]`
- for Polymarket, can use existing evidence score or a deterministic combination of liquidity/freshness/presence of aggregate probability
- for crypto, can use deterministic combination of liquidity/freshness/coverage
- keep this simple and explicit

5. Agreement score:
- bounded in `[0.0, 1.0]`
- higher when families are directionally aligned and both families have decent quality
- lower when mixed/conflicted/unknown
- keep this deterministic and inspectable

6. Confidence score:
- bounded in `[0.0, 1.0]`
- derived from agreement plus evidence-family quality
- should drop when either family is weak/stale/incomplete

7. Alignment classification:
- `aligned`
  - clear directional match with usable quality
- `weakly_aligned`
  - partial match or weaker evidence quality
- `conflicted`
  - directional mismatch with usable quality
- `insufficient`
  - one or both families unknown/incomplete

Use explicit thresholds.

8. Flags:
Surface explicit packet-level flags for cases like:
- `theme_id_mismatch`
- `polymarket_unknown_direction`
- `crypto_unknown_direction`
- `weak_crypto_coverage`
- `stale_polymarket_evidence`
- `stale_crypto_evidence`
- `cross_market_conflict`

9. Explanation:
Produce a short deterministic explanation string summarizing:
- each family direction
- alignment classification
- agreement/confidence
- key flags

## Scoring requirements
Create small pure functions in `scoring.py`.

Suggested functions:
- `derive_polymarket_direction(...)`
- `derive_crypto_direction(...)`
- `compute_agreement_score(...)`
- `compute_comparison_confidence_score(...)`
- `classify_alignment(...)`

Keep them:
- deterministic
- bounded
- easy to inspect
- free of side effects

No randomization.
No hidden global time.
No network assumptions.

## Test requirements

### `test_comparison_models.py`
Cover:
- valid comparison models
- bounded scores rejected if invalid
- invalid alignment/direction rejected

### `test_comparison_comparator.py`
Cover:
- matching theme ids required
- aligned case produces `aligned`
- weaker alignment produces `weakly_aligned`
- directional mismatch produces `conflicted`
- missing/unknown family produces `insufficient`
- packet flags deterministic
- explanation string deterministic

### `test_comparison_scoring.py`
Cover:
- Polymarket direction thresholds deterministic
- crypto direction derivation deterministic for known proxy mixes
- agreement score bounded in `[0,1]`
- confidence score bounded in `[0,1]`
- alignment thresholds deterministic

## Fixtures
Create a small deterministic fixture set with at least:
- one aligned comparison input
- one weakly aligned input
- one conflicted input
- one insufficient input

These can be JSON representations of `ThemeEvidencePacket` and `ThemeCryptoEvidencePacket` shaped inputs.

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement reasoning/policy/trading in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/comparison/*` exists with the files listed above
2. typed models validate correctly
3. comparator consumes `ThemeEvidencePacket` + `ThemeCryptoEvidencePacket`
4. direction derivation is deterministic
5. alignment classification works for aligned / weakly_aligned / conflicted / insufficient
6. agreement and confidence scores are deterministic and bounded
7. explicit flags surface correctly
8. tests pass
9. no unrelated modules were modified
10. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new comparison module if mypy is already in use

At minimum, run:
- targeted pytest for the new comparison tests
- narrow ruff check for touched files
- narrow mypy check for the new comparison module

## Final output format
Return only:
1. concise summary
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. any deviations from spec
6. explicit note whether `src/polymarket_arb/*` was untouched

Do not widen the phase.
Do not start news ingestion.
Do not start reasoning or policy.
Complete only this bounded phase.
