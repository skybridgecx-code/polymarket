# Phase 20C — Operator UI Decision/Status Rendering Surface

## Goal

Surface existing operator review decision/status metadata in local operator UI list/detail views
when companion decision metadata files exist.

This phase is read-only rendering/discovery only.

## Read first

- `.codex/phases/current_phase.md`
- `docs/PHASE_20A_FUTURE_SYSTEM_NEXT_TRACK_SCOPE_LOCK.md`
- `docs/PHASE_20B_OPERATOR_REVIEW_DECISION_METADATA_CONTRACTS.md`
- `src/future_system/operator_review_models/*`
- `src/future_system/operator_ui/artifact_reads.py`
- `src/future_system/operator_ui/render_templates.py`
- `src/future_system/operator_ui/route_handlers.py`
- `tests/future_system/test_operator_ui_review_artifacts.py`
- `tests/future_system/test_operator_ui_integration_flows.py`

## Required deliverable

Add bounded read-only companion metadata discovery/loading and UI rendering support:

- for artifact run id `X`, read companion file `X.operator_review.json` when present
- missing companion metadata file must be optional
- malformed companion metadata must be bounded and must not break existing artifact rendering

Render in operator UI:

- list row review state: `pending` / `decided` / `no-review-metadata`
- detail view review metadata:
  - review status
  - operator decision
  - review notes summary
  - reviewer identity
  - decided/updated timestamps (if present)

Preserve current success/failure-stage outcome rendering and local artifact-file behavior.

## Hard constraints

Do not:

- touch `src/polymarket_arb/*`
- add DB/queues/background jobs/scheduling/delivery/inbox/execution/trading logic
- add UI editing/write flow (read-only only)
- widen scope beyond local artifact-file discovery + rendering

## Tests required

Add deterministic tests for:

- artifact with no decision metadata renders normally
- valid pending metadata appears in list/detail
- valid decided metadata appears in list/detail
- malformed decision metadata is bounded and does not break artifact display
- no reads outside configured root

## Validation

Run:

- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_ui_integration_flows.py tests/future_system/test_operator_review_models.py`
- `ruff check src/future_system/operator_ui src/future_system/operator_review_models tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_ui_integration_flows.py tests/future_system/test_operator_review_models.py`
- `mypy src/future_system/operator_ui src/future_system/operator_review_models`

## Required Codex return format

Return:

1. concise summary
2. exact files changed
3. validation output
4. risks/deferred items
5. do not commit unless asked
