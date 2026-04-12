# Phase 18H — Candidate Signal Contract + Ranking

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
- This phase adds the candidate signal layer that turns those upstream packets into a canonical ranked opportunity surface.
- This phase is deterministic aggregation and ranking only.
- Do not add news, LLM reasoning, policy, execution, UI, storage, schedulers, or live network logic.

## Why this phase exists
The system can now:
- define a theme
- assemble Polymarket evidence
- detect internal divergence
- assemble crypto evidence
- compare Polymarket vs crypto

But it still cannot answer:
- is this worth surfacing as a candidate
- is it a weak watch item or a strong candidate
- is it internally conflicted and unsafe
- how should multiple candidates be ranked against each other

This phase creates the first canonical opportunity surface.

## Phase objective
Build `src/future_system/candidates/` so the system can:

1. accept canonical upstream packets for one theme:
   - `ThemeLinkPacket`
   - `ThemeEvidencePacket`
   - `ThemeDivergencePacket`
   - `ThemeCryptoEvidencePacket`
   - `ThemeComparisonPacket`
2. compute a deterministic candidate score
3. classify candidate posture:
   - `watch`
   - `candidate`
   - `high_conflict`
   - `insufficient`
4. emit a canonical `CandidateSignalPacket`
5. rank multiple candidate packets deterministically

This phase does not do LLM reasoning.
This phase does not make policy decisions.
This phase does not execute trades.

## In scope

Create these files if they do not already exist:

- `src/future_system/candidates/__init__.py`
- `src/future_system/candidates/models.py`
- `src/future_system/candidates/builder.py`
- `src/future_system/candidates/scoring.py`
- `src/future_system/candidates/ranker.py`

Create tests:

- `tests/future_system/test_candidates_models.py`
- `tests/future_system/test_candidates_builder.py`
- `tests/future_system/test_candidates_scoring.py`
- `tests/future_system/test_candidates_ranker.py`

Create fixtures:

- `tests/fixtures/future_system/candidates/candidate_inputs.json`

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

### 1. `CandidatePosture`
Use an enum or literal model for:
- `watch`
- `candidate`
- `high_conflict`
- `insufficient`

### 2. `CandidateReasonCode`
Use an enum or literal model for explicit reasons such as:
- `strong_cross_market_alignment`
- `weak_cross_market_alignment`
- `cross_market_conflict`
- `high_internal_divergence`
- `weak_liquidity`
- `stale_evidence`
- `weak_crypto_coverage`
- `missing_probability_inputs`
- `insufficient_comparison_confidence`

You may add a few more if needed, but keep the set small and explicit.

### 3. `CandidateSignalPacket`
Canonical candidate output for one theme.

Suggested fields:
- `theme_id: str`
- `title: str | None`
- `posture: CandidatePosture`
- `candidate_score: float`
- `confidence_score: float`
- `conflict_score: float`
- `alignment: str`
- `primary_market_slug: str | None`
- `primary_symbol: str | None`
- `reason_codes: list[CandidateReasonCode | str]`
- `flags: list[str]`
- `explanation: str`

### 4. `CandidateBuildError`
Raised when candidate construction cannot be computed from the provided packets.

### 5. `CandidateRankEntry`
Optional helper model if useful for ranking output.

## Candidate build behavior

Implement deterministic candidate construction from:
- `ThemeLinkPacket`
- `ThemeEvidencePacket`
- `ThemeDivergencePacket`
- `ThemeCryptoEvidencePacket`
- `ThemeComparisonPacket`

Rules:

1. Theme ids must match across all inputs.
   - if they do not, raise `CandidateBuildError`

2. `candidate_score` must be bounded in `[0.0, 1.0]`
   and should reward:
   - higher cross-market agreement
   - better comparison confidence
   - better evidence freshness/liquidity
   - better crypto coverage

   and penalize:
   - higher internal divergence
   - cross-market conflict
   - stale / weak evidence
   - insufficient comparison quality

Keep this formula explicit and simple.
Do not invent a fake quant model.

3. `conflict_score` must be bounded in `[0.0, 1.0]`
   and should primarily reflect:
   - divergence score
   - comparison alignment conflict
   - serious evidence flags

4. `confidence_score` should be deterministic and bounded in `[0.0, 1.0]`
   using available upstream confidence/quality signals.
   It should drop when inputs are stale, incomplete, or conflicting.

5. Candidate posture classification:
   - `candidate`
     - strong enough candidate score
     - no major conflict
     - not insufficient
   - `watch`
     - usable but weaker
     - moderate score or weaker quality
   - `high_conflict`
     - serious divergence or cross-market conflict
   - `insufficient`
     - missing or weak comparison / evidence / aggregate quality

Use explicit thresholds.

6. `alignment` should reflect the upstream comparison alignment value directly or in a normalized string form.

7. `title`
   - may be taken from `ThemeLinkPacket`/theme metadata if available
   - if not available, allow `None`
   - do not fabricate titles from nowhere

8. `reason_codes`
   - derive deterministically from upstream packet state
   - include the most important reasons only
   - keep the list short and explicit

9. `flags`
   - carry forward important upstream flags where useful
   - do not blindly dump every upstream flag if that becomes noisy
   - keep deterministic and useful

10. `explanation`
   Produce a short deterministic explanation string summarizing:
   - posture
   - candidate/confidence/conflict scores
   - alignment
   - top reason codes

## Ranking behavior

Implement deterministic ranking over multiple `CandidateSignalPacket` values.

Rules:

1. Primary sort:
   - higher `candidate_score` first

2. Secondary sort:
   - lower `conflict_score` first

3. Tertiary sort:
   - higher `confidence_score` first

4. Final tie-break:
   - `theme_id` ascending

5. Optionally expose a helper that filters to only non-`insufficient` candidates before ranking, but keep this small and explicit.

## Scoring requirements
Create small pure functions in `scoring.py`.

Suggested functions:
- `compute_candidate_score(...)`
- `compute_candidate_confidence_score(...)`
- `compute_candidate_conflict_score(...)`
- `classify_candidate_posture(...)`
- `derive_candidate_reason_codes(...)`

Keep them:
- deterministic
- bounded
- easy to inspect
- free of side effects

No randomization.
No hidden global time.
No network assumptions.

## Test requirements

### `test_candidates_models.py`
Cover:
- valid candidate models
- invalid bounded scores rejected
- invalid posture rejected

### `test_candidates_builder.py`
Cover:
- matching theme ids required
- strong aligned case yields `candidate`
- weaker case yields `watch`
- conflict case yields `high_conflict`
- insufficient case yields `insufficient`
- reason codes deterministic
- explanation deterministic
- important upstream flags propagate appropriately

### `test_candidates_scoring.py`
Cover:
- candidate score bounded in `[0,1]`
- confidence score bounded in `[0,1]`
- conflict score bounded in `[0,1]`
- posture thresholds deterministic

### `test_candidates_ranker.py`
Cover:
- ranking order uses candidate score first
- lower conflict wins tie
- higher confidence wins next tie
- theme_id ascending is final tie-break
- optional insufficient filtering behavior is deterministic if implemented

## Fixtures
Create a small deterministic fixture set with at least:
- one strong candidate case
- one watch case
- one high-conflict case
- one insufficient case

These can be JSON representations of the upstream packet inputs needed to build candidates.

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement reasoning/policy/trading in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/candidates/*` exists with the files listed above
2. typed models validate correctly
3. builder consumes the canonical upstream packets
4. candidate/confidence/conflict scores are deterministic and bounded
5. posture classification works for watch / candidate / high_conflict / insufficient
6. ranking is deterministic
7. reason codes and flags surface correctly
8. tests pass
9. no unrelated modules were modified
10. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new candidates module if mypy is already in use

At minimum, run:
- targeted pytest for the new candidates tests
- narrow ruff check for touched files
- narrow mypy check for the new candidates module

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
Do not start reasoning or policy.
Complete only this bounded phase.
