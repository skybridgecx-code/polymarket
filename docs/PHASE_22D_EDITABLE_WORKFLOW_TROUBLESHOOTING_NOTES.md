# Phase 22D Editable Workflow Troubleshooting Notes

## Scope

Operator recovery notes for the local editable operator decision workflow.

This is docs-only. No runtime behavior changes.

## Troubleshooting Matrix

### 1. Missing companion metadata

Symptom:

- update fails with `Review Update Error`
- message includes `operator_review_metadata_missing`

Likely cause:

- artifacts were generated without `--initialize-operator-review`
- `X.operator_review.json` was deleted or never created

Recovery:

- regenerate artifacts with `--initialize-operator-review`, or
- create companion metadata through the supported CLI initialization path

Do not manually edit base artifact `.json` / `.md` files to fake review state.

### 2. Malformed companion metadata

Symptom:

- list/detail still load artifact content
- metadata area shows bounded invalid metadata state
- update may fail with `operator_review_metadata_invalid`

Likely cause:

- `X.operator_review.json` contains invalid JSON
- payload does not validate as `OperatorReviewDecisionRecord`

Recovery:

- inspect `X.operator_review.json`
- restore from a known-good artifact set, or
- regenerate the run with `--initialize-operator-review` if overwriting/removing the bad local artifact set is acceptable

### 3. Existing companion metadata no-overwrite behavior

Symptom:

- CLI with `--initialize-operator-review` fails
- error mentions existing operator review metadata

Likely cause:

- `X.operator_review.json` already exists
- CLI refuses to silently overwrite operator review state

Recovery:

- inspect the existing companion metadata
- use the local UI update flow for decision changes
- only remove/regenerate local artifact files when intentionally resetting the local review state

### 4. Target subdirectory issue

Symptom:

- detail/update route fails with target subdirectory error
- triggered run exists but is not visible in top-level list

Likely cause:

- UI trigger wrote artifacts under `operator_runs` or another safe subdirectory
- list view reads only non-recursive files at the configured root
- target subdirectory includes invalid segments, `..`, or absolute path behavior

Recovery:

- use the redirected detail URL with `target_subdirectory`
- keep target subdirectories relative and safe
- inspect the actual artifact directory under the configured root

### 5. Invalid artifacts root

Symptom:

- UI shows root unavailable
- trigger/update/read actions fail with artifacts root error

Likely cause:

- `FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT` is unset
- path does not exist
- path is not a directory
- directory lacks read/write/execute permissions

Recovery:

- export `FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT` to an existing writable directory
- verify permissions
- restart the local operator UI

### 6. Failed POST update

Symptom:

- form submission returns `Review Update Error`

Likely causes:

- missing companion metadata
- malformed companion metadata
- invalid decision/status combination
- unsafe path or target subdirectory

Recovery:

- verify `X.operator_review.json` exists
- verify it validates as operator review metadata
- if setting `review_status=decided`, choose a valid `operator_decision`
- retry from the run detail page

## Safety Reminder

The editable workflow remains local and file-based.

It does not:

- place trades
- execute orders
- notify anyone
- enqueue jobs
- write to a database
- integrate with `src/polymarket_arb/*`
