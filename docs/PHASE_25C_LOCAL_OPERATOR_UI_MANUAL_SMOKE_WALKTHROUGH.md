# Phase 25C — Local Operator UI Manual Smoke Walkthrough

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-25c-local-operator-ui-manual-smoke-walkthrough`
- Phase: `25C — local operator UI manual smoke walkthrough`
- Source checkpoint: `phase-25b-local-operator-ui-evidence-inventory`

## Purpose
This phase defines the exact manual smoke walkthrough for capturing evidence of the shipped `future_system` local operator UI workflow. It is a docs-only phase and does not change runtime behavior.

## Boundaries
- Docs-only phase.
- No runtime code changes.
- No test changes.
- No template or UI copy changes.
- No changes under `src/polymarket_arb/*`.
- No infrastructure, DB, queue, scheduling, notification, inbox, or production-trading work.

## Preconditions
Before starting the walkthrough:
1. Work from the shipped local artifact-file workflow only.
2. Ensure the repo state is clean.
3. Ensure local review artifacts are available for:
   - a populated operator review metadata case
   - an empty or missing metadata case, if available
4. Be ready to record:
   - screenshot filenames
   - artifact/sample paths used
   - any commands used to launch the local UI or prepare artifacts

## Recommended evidence folder structure
Use a simple local folder structure for manual evidence collection:
- `evidence/local-operator-ui/`
  - `01-list-page.png`
  - `02-create-section.png`
  - `03-detail-page.png`
  - `04-populated-review.png`
  - `05-empty-review.png`
  - `06-update-decision-form.png`
  - `07-post-update-state.png`
  - `notes.md`

This structure is only a documentation recommendation for consistency.

## Manual smoke walkthrough

### Step 1 — confirm repo checkpoint
Record:
- current branch
- current HEAD
- clean working tree status

Expected outcome:
- you are on the intended evidence-capture branch and the tree is clean

### Step 2 — prepare or identify local review artifacts
Record:
- artifact directory path
- whether the selected example is populated or empty-state oriented

Expected outcome:
- at least one artifact set exists that can drive the operator UI detail view

### Step 3 — open the Local Review Runs list page
Capture:
- page title `Local Review Runs`
- visible run list/table
- table caption

Expected outcome:
- list page loads and shows the shipped list layout

### Step 4 — capture the Create Local Review Run section
Capture:
- section title `Create Local Review Run`
- visible form controls
- helper text or error state if present

Expected outcome:
- the shipped trigger/create entry surface is visible and understandable

### Step 5 — open a Local Review Run detail page
Capture:
- page title `Local Review Run Detail`
- back link `Back to local review runs`
- main detail content

Expected outcome:
- detail page loads and preserves the shipped information architecture

### Step 6 — capture populated Operator Decision Review state
Capture:
- `Operator Decision Review` heading
- rendered populated metadata values

Expected outcome:
- operator review metadata is visible in the populated case

### Step 7 — capture empty metadata state if available
Capture:
- `No review metadata` label

Expected outcome:
- explicit empty-state wording is visible for the missing metadata case

### Step 8 — capture the Update Decision form
Capture:
- `Update Decision` heading
- form field grouping
- helper text
- `Save Local Decision` button

Expected outcome:
- editable decision form is visible with the shipped wording and accessibility-oriented structure

### Step 9 — exercise a local decision update if appropriate
Record:
- what was changed
- which local artifact/file was updated

Capture:
- post-submit detail state showing updated metadata

Expected outcome:
- updated review metadata is visible after save

### Step 10 — write notes for evidence traceability
Record in `notes.md`:
- screenshot filenames and what each shows
- artifact/sample paths used
- command history or launch commands used
- any gaps, such as unavailable empty-state or skipped update flow

Expected outcome:
- evidence can be understood later without reconstructing the session from memory

## Smoke pass criteria
A manual smoke pass is considered complete when:
- the list page was captured
- the create section was captured
- the detail page was captured
- the populated review state was captured
- the empty review state was captured if available
- the update decision form was captured
- the post-update persisted state was captured if the update flow was exercised
- notes exist tying screenshots to artifact/sample context

## Failure handling notes
If a required screen cannot be captured:
- do not change runtime code in this phase
- record the missing evidence item
- record whether the issue is:
  - missing sample data
  - local launch/setup issue
  - genuine shipped UI problem
- defer any runtime fix work to a separately scoped future phase

## Deliverable
- A docs-only manual smoke walkthrough for collecting operator UI evidence consistently.

## Exit criteria
- Walkthrough steps are explicit and ordered.
- Preconditions are explicit.
- Expected outcomes are explicit.
- Smoke pass criteria are explicit.
- Failure handling stays within docs/evidence boundaries.
- No runtime behavior has changed.
