# Phase 18M — Policy Engine Contracts + Decision Layer

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
- `src/future_system/news_adapter/*` is the normalized news source boundary.
- `src/future_system/news_evidence/*` is the theme-linked news evidence layer.
- `src/future_system/context_bundle/*` is the canonical bundled operator/reasoning input.
- `src/future_system/reasoning_contracts/*` is the strict reasoning interface.
- This phase adds the deterministic policy layer that consumes bundled context + validated reasoning output and emits a canonical decision packet.
- This phase does not execute trades.
- Do not add execution logic, UI, storage, schedulers, or live network logic.

## Why this phase exists
The system now has:
- structured market evidence
- structured news evidence
- deterministic cross-market comparison
- deterministic candidate ranking
- strict reasoning input/output contracts

But it still lacks the final deterministic gate that decides:
- is this allowed forward
- should it be held for more evidence
- should it be denied because the setup is too weak or conflicted

Without that layer, the architecture is incomplete.

## Phase objective
Build `src/future_system/policy_engine/` so the system can:

1. accept an `OpportunityContextBundle`
2. accept a validated `ReasoningOutputPacket`
3. compute deterministic policy scores and readiness
4. classify final decision:
   - `allow`
   - `hold`
   - `deny`
5. emit a canonical `PolicyDecisionPacket`
6. surface explicit deterministic reason codes

This phase does not execute anything.
This phase does not call an LLM.
This phase does not place trades.

## In scope

Create these files if they do not already exist:

- `src/future_system/policy_engine/__init__.py`
- `src/future_system/policy_engine/models.py`
- `src/future_system/policy_engine/engine.py`
- `src/future_system/policy_engine/scoring.py`

Create tests:

- `tests/future_system/test_policy_engine_models.py`
- `tests/future_system/test_policy_engine_engine.py`
- `tests/future_system/test_policy_engine_scoring.py`

Create fixtures:

- `tests/fixtures/future_system/policy/policy_inputs.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- execution logic
- broker/order logic
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

### 1. `PolicyDecisionAction`
Use an enum or literal model for:
- `allow`
- `hold`
- `deny`

### 2. `PolicyReasonCode`
Use an enum or literal model for explicit reasons such as:
- `strong_candidate_alignment`
- `reasoning_supportive`
- `weak_candidate_score`
- `weak_confidence`
- `high_conflict`
- `candidate_insufficient`
- `comparison_conflicted`
- `reasoning_high_conflict`
- `missing_information_significant`
- `insufficient_news_support`
- `stale_context`
- `bundle_incomplete`
- `reasoning_posture_deny`
- `reasoning_posture_insufficient`

Keep the set small and explicit. Add a few more only if truly necessary.

### 3. `PolicyDecisionPacket`
Canonical deterministic policy output.

Suggested fields:
- `theme_id: str`
- `decision: PolicyDecisionAction`
- `decision_score: float`
- `readiness_score: float`
- `risk_penalty: float`
- `reason_codes: list[PolicyReasonCode | str]`
- `flags: list[str]`
- `summary: str`

All scores must be bounded in `[0.0, 1.0]`.

### 4. `PolicyDecisionError`
Raised when policy decision cannot be computed from the provided bundle/reasoning inputs.

## Policy engine behavior

Implement deterministic policy construction from:
- `OpportunityContextBundle`
- `ReasoningOutputPacket`

Rules:

1. Theme ids must match.
   - if they do not, raise `PolicyDecisionError`

2. `decision_score`
- bounded in `[0.0, 1.0]`
- should reward:
  - stronger candidate score
  - stronger context confidence
  - aligned comparison
  - supportive reasoning posture
  - stronger readiness/completeness
- should penalize:
  - higher conflict score
  - conflicting comparison
  - reasoning posture of `deny` or `high_conflict`
  - bundle weakness / stale context / missing info

Keep this formula explicit and small.
Do not invent a fake quant model.

3. `readiness_score`
- bounded in `[0.0, 1.0]`
- should reflect whether the context is sufficiently complete and usable
- draw from bundle completeness/freshness/confidence and reasoning quality fields
- keep simple and explicit

4. `risk_penalty`
- bounded in `[0.0, 1.0]`
- should reflect:
  - context conflict
  - candidate conflict
  - comparison conflict
  - strong negative reasoning signals
  - significant missing information or uncertainty
- keep simple and explicit

5. Decision classification:
- `allow`
  - strong decision score
  - adequate readiness
  - low enough risk penalty
  - no major deny-style reason present
- `hold`
  - middling setup, incomplete setup, or unresolved tension
- `deny`
  - weak score, low readiness, or high conflict/risk
  - or reasoning posture explicitly denies

Use explicit thresholds in code.

6. `reason_codes`
- derive deterministically from bundle + reasoning state
- include only the most important reasons
- keep the list short and explicit

7. `flags`
- carry forward only important bundle/reasoning flags
- do not dump every upstream flag blindly
- keep deterministic and useful

8. `summary`
Produce a short deterministic summary string including:
- theme id
- final decision
- decision/readiness/risk scores
- top reason codes

## Scoring requirements
Create small pure functions in `scoring.py`.

Suggested functions:
- `compute_policy_decision_score(...)`
- `compute_policy_readiness_score(...)`
- `compute_policy_risk_penalty(...)`
- `classify_policy_decision(...)`
- `derive_policy_reason_codes(...)`

Keep them:
- deterministic
- bounded
- easy to inspect
- free of side effects

No randomization.
No hidden global time.
No network assumptions.

## Handling reasoning output
Use validated `ReasoningOutputPacket` only.
Do not attempt to repair invalid reasoning output here.
Assume parser already enforced schema.

You may deterministically interpret fields like:
- `recommended_posture`
- number of `missing_information` items
- number of `uncertainty_notes` items
- `analyst_flags`

Keep interpretation small and explicit.

## Test requirements

### `test_policy_engine_models.py`
Cover:
- valid decision models
- invalid bounded scores rejected
- invalid decision rejected

### `test_policy_engine_engine.py`
Cover:
- matching theme ids required
- strong supportive case yields `allow`
- middling / incomplete case yields `hold`
- high-conflict / deny-style case yields `deny`
- reason codes deterministic
- summary deterministic
- important bundle/reasoning flags propagate appropriately

### `test_policy_engine_scoring.py`
Cover:
- decision score bounded in `[0,1]`
- readiness score bounded in `[0,1]`
- risk penalty bounded in `[0,1]`
- explicit thresholds yield deterministic decisions for known inputs

## Fixtures
Create a small deterministic fixture set with at least:
- one `allow` case
- one `hold` case
- one `deny` case

These can be JSON representations of:
- `OpportunityContextBundle`
- `ReasoningOutputPacket`

needed to compute the policy decision.

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement execution/trading in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/policy_engine/*` exists with the files listed above
2. typed models validate correctly
3. engine consumes `OpportunityContextBundle` + `ReasoningOutputPacket`
4. decision/readiness/risk scores are deterministic and bounded
5. decision classification works for allow / hold / deny
6. reason codes and flags surface correctly
7. summary is deterministic
8. tests pass
9. no unrelated modules were modified
10. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new policy_engine module if mypy is already in use

At minimum, run:
- targeted pytest for the new policy_engine tests
- narrow ruff check for touched files
- narrow mypy check for the new policy_engine module

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
Do not start execution.
Complete only this bounded phase.
