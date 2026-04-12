# Phase 18N — End-to-End Analysis Runtime (dry-run only)

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
- `src/future_system/policy_engine/*` is the deterministic decision gate.
- This phase adds the dry-run runtime that wires those layers together through a pluggable analyst interface.
- This phase does not perform live model calls.
- This phase does not execute trades.
- Do not add scheduling, UI, persistence, or live network logic.

## Why this phase exists
The architecture is complete in pieces, but the system still lacks one bounded runtime proving the full chain works end to end.

Without this phase:
- components are validated only in isolation
- there is no canonical run artifact
- later live model integration will be harder to control
- operator review lacks a single end-to-end dry-run packet

This phase creates that runtime while keeping the analyst pluggable and fully offline for tests.

## Phase objective
Build `src/future_system/runtime/` so the system can:

1. accept an `OpportunityContextBundle`
2. build a `ReasoningInputPacket`
3. render a deterministic prompt packet
4. call a pluggable analyst interface
5. parse the analyst output into a validated `ReasoningOutputPacket`
6. pass bundle + reasoning into the policy engine
7. emit a canonical `AnalysisRunPacket`
8. emit a compact deterministic run summary

This phase is dry-run only.
No live LLM call.
No execution.

## In scope

Create these files if they do not already exist:

- `src/future_system/runtime/__init__.py`
- `src/future_system/runtime/models.py`
- `src/future_system/runtime/protocol.py`
- `src/future_system/runtime/stub_analyst.py`
- `src/future_system/runtime/runner.py`
- `src/future_system/runtime/summary.py`

Create tests:

- `tests/future_system/test_runtime_models.py`
- `tests/future_system/test_runtime_runner.py`
- `tests/future_system/test_runtime_stub_analyst.py`
- `tests/future_system/test_runtime_summary.py`

Create fixtures:

- `tests/fixtures/future_system/runtime/runtime_inputs.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- live LLM client integration
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

### 1. `AnalysisRunStatus`
Use an enum or literal model for:
- `success`
- `failed`

### 2. `AnalysisRunPacket`
Canonical end-to-end dry-run output.

Suggested fields:
- `theme_id: str`
- `status: AnalysisRunStatus`
- `context_bundle: OpportunityContextBundle`
- `reasoning_input: ReasoningInputPacket`
- `rendered_prompt: RenderedPromptPacket | dict | None`
- `reasoning_output: ReasoningOutputPacket`
- `policy_decision: PolicyDecisionPacket`
- `run_flags: list[str]`
- `run_summary: str`

### 3. `AnalysisRunError`
Raised when the runtime cannot complete the dry-run pipeline.

## Analyst protocol

Implement a small protocol/interface in `protocol.py`.

Suggested behavior:
- accepts a `ReasoningInputPacket` and/or rendered prompt packet
- returns model-like output in either mapping or JSON-string form suitable for the existing reasoning parser

Do not add live model transport methods.
Do not add auth.
Do not add retries.

This is an offline pluggable boundary only.

## Stub analyst

Implement `stub_analyst.py` with a deterministic analyst used for tests.

Requirements:
- produce stable output for known reasoning inputs
- can be rule-based
- should reflect input posture/alignment in a simple deterministic way
- must return output that the existing reasoning parser validates

Keep it small and explicit.

## Runner behavior

Implement deterministic `run_analysis_pipeline(...)` from:
- `OpportunityContextBundle`
- analyst implementation conforming to the protocol

Required flow:

1. Build `ReasoningInputPacket` from bundle using existing reasoning builder
2. Render prompt packet using existing renderer
3. Call analyst protocol with the reasoning input or rendered prompt
4. Parse analyst output using existing reasoning parser
5. Build `PolicyDecisionPacket` using existing policy engine
6. Emit `AnalysisRunPacket`

Rules:

- theme id must carry through consistently
- failures in analyst output parsing should raise `AnalysisRunError`
- policy engine should only receive validated reasoning output
- no hidden retries
- no hidden global state
- keep the flow synchronous and explicit

## Run flags

Surface explicit run-level flags such as:
- `analysis_dry_run`
- `stub_analyst_used`
- `reasoning_parsed`
- `policy_computed`

Include failure-related flags if useful in error paths, but keep this small.

## Run summary

Implement one deterministic helper in `summary.py` that produces a compact run summary string including:
- theme id
- candidate posture
- reasoning recommended posture
- final policy decision
- top scores or flags

Keep it short, stable, and explicit.

## Test requirements

### `test_runtime_models.py`
Cover:
- valid run models
- invalid status rejected if applicable
- required fields enforced

### `test_runtime_stub_analyst.py`
Cover:
- stub analyst returns deterministic output
- output shape is parseable by the reasoning parser
- different known input states produce deterministic posture differences if designed that way

### `test_runtime_runner.py`
Cover:
- full dry-run succeeds end to end for valid input
- reasoning input is built deterministically
- prompt packet is rendered deterministically
- parsed reasoning output is validated
- policy decision is computed
- run flags deterministic
- malformed analyst output raises `AnalysisRunError`
- status/error path behavior deterministic

### `test_runtime_summary.py`
Cover:
- run summary deterministic
- summary reflects theme id
- summary reflects reasoning posture
- summary reflects final decision
- summary reflects important flags where applicable

## Fixtures
Create a small deterministic fixture set with at least:
- one successful dry-run input case
- one case used to simulate malformed analyst output handling

Fixtures can include serialized context bundle shapes and/or minimal data required for runner tests.

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement live model calls or execution in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/runtime/*` exists with the files listed above
2. typed models validate correctly
3. runtime consumes `OpportunityContextBundle`
4. runtime uses existing reasoning builder/renderer/parser and policy engine
5. stub analyst is deterministic
6. full dry-run pipeline works end to end
7. malformed analyst output fails cleanly
8. run summary is deterministic
9. tests pass
10. no unrelated modules were modified
11. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new runtime module if mypy is already in use

At minimum, run:
- targeted pytest for the new runtime tests
- narrow ruff check for touched files
- narrow mypy check for the new runtime module

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
Do not start execution.
Complete only this bounded phase.
