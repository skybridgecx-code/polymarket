# Phase 27A — Operator Review Notes / Reviewer Persistence Audit

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-27a-operator-review-notes-reviewer-persistence-audit`
- Phase: `27A — operator review notes / reviewer persistence audit`
- Source checkpoint: `main` at Phase 26B closeout

## Purpose
Phase 26A manual evidence capture recorded an observation that `review_status` and `operator_decision` persisted after saving a local operator decision update, while `review_notes_summary` and `reviewer_identity` were not reflected in the inspected companion metadata output.

This phase audits the shipped code and tests to determine whether that observation represents a confirmed runtime persistence bug.

## Audit findings

### Form route accepts notes and reviewer
`src/future_system/operator_ui/review_artifacts.py` defines the update route with:
- `review_status`
- `operator_decision`
- `review_notes_summary`
- `reviewer_identity`
- `updated_at_epoch_ns`
- `target_subdirectory`

The route passes `review_notes_summary` and `reviewer_identity` into the update request handler.

### Route handler passes notes and reviewer through
`src/future_system/operator_ui/route_handlers.py` passes:
- `review_notes_summary=_empty_to_none(review_notes_summary)`
- `reviewer_identity=_empty_to_none(reviewer_identity)`

into `OperatorReviewUpdateInput`.

### Update helper writes notes and reviewer
`src/future_system/operator_review_models/updates.py` applies and writes:
- `review_notes_summary=update_input.review_notes_summary`
- `reviewer_identity=update_input.reviewer_identity`

### UI template renders notes and reviewer inputs
`src/future_system/operator_ui/render_templates.py` renders:
- `textarea name="review_notes_summary"`
- `input name="reviewer_identity"`

and also renders those fields in the metadata display section.

### Tests already cover persistence
Existing tests assert notes/reviewer persistence:
- `tests/future_system/test_operator_review_update_helpers.py`
- `tests/future_system/test_operator_review_workflow_integration.py`
- `tests/future_system/test_operator_ui_review_artifacts.py`

The tests include cases where:
- `review_notes_summary` persists
- `reviewer_identity` persists
- empty values normalize to `None`
- decided review status requires a decision
- companion metadata rewrite remains deterministic

## Conclusion
The Phase 26A observation is **not a confirmed shipped persistence bug** based on code and test audit.

The existing implementation path appears to support notes/reviewer persistence correctly, and focused tests already assert that behavior.

Most likely explanations for the manual observation:
- the manual form fields were not populated before save
- the browser submitted a different state than expected
- the inspected metadata file was not the same file updated by the form
- the page/server was still affected by the earlier artifacts-root/server mismatch during manual testing

## Scope decision
No runtime fix should be made in this phase.

## Optional future follow-up
A separate manual reproduction phase may be opened if needed:
- create a fresh artifact root
- launch one server only
- initialize companion metadata
- submit a decision update with notes and reviewer
- inspect the exact companion file immediately after save

Only if that controlled reproduction fails should a runtime bug-fix phase be opened.

## Boundaries preserved
- No runtime code changes.
- No UI template changes.
- No test changes.
- No changes under `src/polymarket_arb/*`.
- No DB, queue, scheduling, notification, inbox, background-job, or production-trading work.

## Exit criteria
- Persistence path audited.
- Existing test coverage identified.
- Manual observation classified.
- No speculative runtime fix introduced.
