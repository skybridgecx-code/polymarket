# Phase 18L — Reasoning Contracts + Prompt Packet

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
- This phase adds the deterministic reasoning interface: contracts, prompt packet rendering, and output validation.
- This phase does not call an LLM.
- Do not add policy, execution, UI, storage, schedulers, or live network logic.

## Why this phase exists
The system now has a stable `OpportunityContextBundle`, but there is still no safe interface between that deterministic bundle and future AI reasoning.

Without this layer:
- prompt shapes will drift
- reasoning outputs will be inconsistent
- downstream policy will receive unstable analyst outputs
- future LLM integrations will be hard to validate

This phase creates:
- a canonical reasoning input packet
- a deterministic prompt renderer
- a strict reasoning output schema
- a parser/validator for model responses

## Phase objective
Build `src/future_system/reasoning_contracts/` so the system can:

1. accept an `OpportunityContextBundle`
2. build a canonical `ReasoningInputPacket`
3. render a deterministic prompt packet/string for later LLM use
4. validate a strict `ReasoningOutputPacket`
5. parse model-like JSON output safely into the strict schema

This phase does not execute model calls.
This phase does not make policy decisions.
This phase does not perform trading.

## In scope

Create these files if they do not already exist:

- `src/future_system/reasoning_contracts/__init__.py`
- `src/future_system/reasoning_contracts/models.py`
- `src/future_system/reasoning_contracts/builder.py`
- `src/future_system/reasoning_contracts/renderer.py`
- `src/future_system/reasoning_contracts/parser.py`

Create tests:

- `tests/future_system/test_reasoning_contracts_models.py`
- `tests/future_system/test_reasoning_contracts_builder.py`
- `tests/future_system/test_reasoning_contracts_renderer.py`
- `tests/future_system/test_reasoning_contracts_parser.py`

Create fixtures:

- `tests/fixtures/future_system/reasoning/reasoning_inputs.json`
- `tests/fixtures/future_system/reasoning/reasoning_outputs.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- live LLM calls
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

### 1. `ReasoningRecommendedPosture`
Use an enum or literal model for:
- `watch`
- `candidate`
- `high_conflict`
- `deny`
- `insufficient`

### 2. `ReasoningInputPacket`
Canonical reasoning input built from `OpportunityContextBundle`.

Suggested fields:
- `theme_id: str`
- `title: str | None`
- `candidate_posture: str`
- `comparison_alignment: str`
- `candidate_score: float`
- `confidence_score: float`
- `conflict_score: float`
- `bundle_flags: list[str]`
- `operator_summary: str`
- `structured_facts: dict[str, object]`
- `prompt_version: str`

Notes:
- `structured_facts` should contain a compact, stable subset of the bundle’s load-bearing facts
- do not dump the entire bundle blindly
- keep it deterministic and compact

### 3. `ReasoningOutputPacket`
Strict validated reasoning output schema.

Suggested fields:
- `theme_id: str`
- `thesis: str`
- `counter_thesis: str`
- `key_drivers: list[str]`
- `missing_information: list[str]`
- `uncertainty_notes: list[str]`
- `recommended_posture: ReasoningRecommendedPosture`
- `confidence_explanation: str`
- `analyst_flags: list[str]`

Validation:
- non-empty thesis/counter_thesis/confidence_explanation
- `key_drivers` length >= 1
- lists should be normalized string lists
- keep it strict but practical

### 4. `RenderedPromptPacket`
Optional helper model if useful.

Suggested fields:
- `system_prompt: str`
- `user_prompt: str`
- `rendered_json_schema: dict[str, object] | None`

### 5. `ReasoningParseError`
Raised when model-like output cannot be parsed into a valid `ReasoningOutputPacket`.

## Builder behavior

Implement deterministic construction of `ReasoningInputPacket` from `OpportunityContextBundle`.

Rules:

1. Theme id must carry through exactly.
2. `structured_facts` must be compact and stable.
   Include only load-bearing facts, for example:
   - candidate posture
   - candidate/comparison/conflict scores
   - comparison alignment
   - primary market slug
   - primary symbol
   - news matched count / official-source presence
   - key bundle flags
3. Do not include verbose redundant blobs.
4. `prompt_version` should be explicit and hard-coded for now, e.g. `"v1"`.

## Renderer behavior

Implement deterministic prompt rendering from `ReasoningInputPacket`.

Rules:

1. Render a small stable system prompt that instructs the future model to behave as an analyst, not an oracle.
2. Render a stable user prompt that:
   - includes the relevant structured facts
   - asks for thesis, counter-thesis, missing info, uncertainty, recommended posture, and confidence explanation
   - instructs strict JSON output
3. Keep prompts compact and deterministic.
4. Optionally expose a JSON-schema-like dict describing the expected output shape.
5. No templating engine required. Keep it explicit in code.

## Parser behavior

Implement deterministic parsing/validation from:
- Python mapping
- JSON string

Rules:

1. Parse model-like JSON safely into `ReasoningOutputPacket`
2. Reject malformed JSON with `ReasoningParseError`
3. Reject schema-invalid outputs with `ReasoningParseError`
4. Normalize string lists deterministically:
   - trim whitespace
   - discard empty strings
   - preserve order
5. Do not auto-heal missing required fields
6. Do not silently coerce invalid posture values

## Summary / contract behavior
Expose helpers that make this future interface easy to use:
- build reasoning input from bundle
- render prompt packet from reasoning input
- parse reasoning output into strict schema

Keep them:
- deterministic
- explicit
- free of side effects

## Test requirements

### `test_reasoning_contracts_models.py`
Cover:
- valid input/output models
- invalid posture rejected
- required non-empty fields enforced
- list normalization deterministic

### `test_reasoning_contracts_builder.py`
Cover:
- input packet builds successfully from valid context bundle
- theme id/title/operator summary carry through deterministically
- structured facts remain compact and stable
- prompt version deterministic

### `test_reasoning_contracts_renderer.py`
Cover:
- rendered prompts deterministic
- rendered prompts include key fields
- rendered JSON schema/output shape deterministic if implemented
- system prompt and user prompt stay stable for known input

### `test_reasoning_contracts_parser.py`
Cover:
- valid mapping parses
- valid JSON string parses
- malformed JSON raises `ReasoningParseError`
- invalid posture raises `ReasoningParseError`
- missing required fields raise `ReasoningParseError`
- normalized string lists deterministic

## Fixtures
Create small deterministic fixture sets with at least:
- one valid reasoning input built from a realistic context bundle shape
- one valid reasoning output example
- one malformed/invalid output example

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement live LLM calls, policy, or trading in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/reasoning_contracts/*` exists with the files listed above
2. typed models validate correctly
3. builder consumes `OpportunityContextBundle`
4. renderer emits deterministic prompt packets/strings
5. parser validates strict reasoning outputs deterministically
6. output schema is explicit and stable
7. tests pass
8. no unrelated modules were modified
9. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new reasoning_contracts module if mypy is already in use

At minimum, run:
- targeted pytest for the new reasoning_contracts tests
- narrow ruff check for touched files
- narrow mypy check for the new reasoning_contracts module

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
Do not start live model calls.
Do not start policy or execution.
Complete only this bounded phase.
