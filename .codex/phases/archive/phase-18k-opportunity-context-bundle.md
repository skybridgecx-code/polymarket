# Phase 18K — Opportunity Context Bundle

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
- This phase adds a deterministic context-bundle layer that packages all canonical upstream packets into one stable operator/reasoning input.
- This phase is bundling, completeness scoring, and deterministic summary only.
- Do not add reasoning, prompts, policy, execution, UI, storage, schedulers, or live network logic.

## Why this phase exists
The system now has many clean packet types, but they are still separate.

That is a problem because:
- future reasoning should not read seven packet types directly
- operator review should not require manual stitching
- logging/export surfaces need one stable artifact
- later LLM prompts should consume one canonical input, not raw scattered structures

This phase creates that canonical bundle.

## Phase objective
Build `src/future_system/context_bundle/` so the system can:

1. accept canonical upstream packets for one theme:
   - `ThemeLinkPacket`
   - `ThemeEvidencePacket`
   - `ThemeDivergencePacket`
   - `ThemeCryptoEvidencePacket`
   - `ThemeComparisonPacket`
   - `ThemeNewsEvidencePacket`
   - `CandidateSignalPacket`
2. validate theme consistency across all inputs
3. compute deterministic bundle completeness / quality summaries
4. emit one canonical `OpportunityContextBundle`
5. emit a short deterministic operator summary string
6. expose a stable dict/JSON-ready export shape

This phase does not do LLM reasoning.
This phase does not make policy decisions.
This phase does not execute trades.

## In scope

Create these files if they do not already exist:

- `src/future_system/context_bundle/__init__.py`
- `src/future_system/context_bundle/models.py`
- `src/future_system/context_bundle/builder.py`
- `src/future_system/context_bundle/summary.py`

Create tests:

- `tests/future_system/test_context_bundle_models.py`
- `tests/future_system/test_context_bundle_builder.py`
- `tests/future_system/test_context_bundle_summary.py`

Create fixtures:

- `tests/fixtures/future_system/context_bundle/context_bundle_inputs.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

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

### 1. `BundleComponentStatus`
Use an enum or literal model for:
- `present`
- `partial`
- `missing`

### 2. `BundleQualitySummary`
Represents deterministic bundle-level quality information.

Suggested fields:
- `completeness_score: float`
- `freshness_score: float`
- `confidence_score: float`
- `conflict_score: float`
- `component_statuses: dict[str, BundleComponentStatus]`
- `flags: list[str]`

All bounded scores must be within `[0.0, 1.0]`.

### 3. `OpportunityContextBundle`
Canonical bundled context for one theme.

Suggested fields:
- `theme_id: str`
- `title: str | None`
- `theme_link: ThemeLinkPacket`
- `polymarket_evidence: ThemeEvidencePacket`
- `divergence: ThemeDivergencePacket`
- `crypto_evidence: ThemeCryptoEvidencePacket`
- `comparison: ThemeComparisonPacket`
- `news_evidence: ThemeNewsEvidencePacket`
- `candidate: CandidateSignalPacket`
- `quality: BundleQualitySummary`
- `operator_summary: str`
- `flags: list[str]`

### 4. `ContextBundleError`
Raised when the bundle cannot be built from the provided packets.

## Bundle build behavior

Implement deterministic bundle construction from the seven canonical packet types listed above.

Rules:

1. Theme ids must match across all inputs.
   - if they do not, raise `ContextBundleError`

2. `title`
   - may come from the theme-linked packet or another upstream source if available
   - if unavailable, allow `None`
   - do not fabricate titles

3. Component statuses:
   Determine status for each family at minimum:
   - `theme_link`
   - `polymarket_evidence`
   - `divergence`
   - `crypto_evidence`
   - `comparison`
   - `news_evidence`
   - `candidate`

Use small explicit deterministic rules.
Examples:
- `present` when required fields and usable scores exist
- `partial` when packet exists but is weak/flagged/incomplete
- `missing` only if a required packet cannot support a usable context state

Because this phase receives canonical packets, `missing` may be uncommon, but allow it when packet contents are effectively unusable.

4. `completeness_score`
- bounded in `[0.0, 1.0]`
- deterministic function of component statuses
- higher when more families are present and usable

5. `freshness_score`
- bounded in `[0.0, 1.0]`
- deterministic aggregation from upstream packet freshness/quality signals
- keep simple and explicit

6. `confidence_score`
- bounded in `[0.0, 1.0]`
- deterministic aggregation from candidate/comparison/news/polymarket/crypto quality signals
- keep simple and explicit

7. `conflict_score`
- bounded in `[0.0, 1.0]`
- deterministic aggregation from divergence + comparison conflict + important negative flags

8. Bundle flags:
Surface explicit packet-level flags for cases like:
- `context_incomplete`
- `stale_context`
- `weak_news_context`
- `weak_crypto_context`
- `cross_market_conflict`
- `high_internal_divergence`
- `candidate_insufficient`

Carry forward only important flags.
Do not dump every upstream flag blindly.

9. `operator_summary`
Produce a short deterministic summary string including:
- theme id
- candidate posture
- comparison alignment
- key scores
- top bundle flags

This summary is for operators and later prompt input.
It must remain deterministic and compact.

10. Export shape
Expose a helper in `builder.py` or `summary.py` that returns a stable dict/JSON-ready representation.
Keep it explicit and deterministic.
No custom serializer framework needed.

## Summary behavior

Implement one small deterministic helper that produces a compact summary string from an `OpportunityContextBundle`.

Keep it:
- stable
- easy to inspect
- free of side effects

No templating engine.
No LLM use.

## Test requirements

### `test_context_bundle_models.py`
Cover:
- valid bundle models
- invalid bounded scores rejected
- invalid component statuses rejected

### `test_context_bundle_builder.py`
Cover:
- matching theme ids required
- bundle builds successfully from valid canonical packets
- completeness/freshness/confidence/conflict scores are bounded
- component statuses deterministic
- important flags propagate appropriately
- export shape deterministic
- title handling deterministic

### `test_context_bundle_summary.py`
Cover:
- operator summary string deterministic
- summary reflects candidate posture
- summary reflects comparison alignment
- summary reflects bundle flags
- edge cases with weak/incomplete contexts remain deterministic

## Fixtures
Create a small deterministic fixture set with at least:
- one strong/complete context
- one weak/incomplete context
- one conflicted context

These can be JSON representations of the upstream canonical packets needed to build the bundle.

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement reasoning/policy/trading in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/context_bundle/*` exists with the files listed above
2. typed models validate correctly
3. builder consumes the canonical upstream packets
4. theme consistency is enforced
5. completeness/freshness/confidence/conflict scores are deterministic and bounded
6. component statuses are deterministic
7. operator summary is deterministic
8. stable export shape exists
9. tests pass
10. no unrelated modules were modified
11. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new context bundle module if mypy is already in use

At minimum, run:
- targeted pytest for the new context bundle tests
- narrow ruff check for touched files
- narrow mypy check for the new context bundle module

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
