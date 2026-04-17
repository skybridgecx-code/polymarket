# Phase 25D — Local Operator UI Release Checklist

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-25d-local-operator-ui-release-checklist`
- Phase: `25D — local operator UI release checklist`
- Source checkpoint: `phase-25c-local-operator-ui-manual-smoke-walkthrough`

## Purpose
This phase defines the final release-style checklist for the shipped `future_system` local operator UI evidence pass. It is a docs-only phase and does not change runtime behavior.

## Boundaries
- Docs-only phase.
- No runtime code changes.
- No template or UI copy changes.
- No test changes.
- No changes under `src/polymarket_arb/*`.
- No DB, queue, scheduling, notification, inbox, or production-trading work.

## Release-style checklist

### 1. Repo checkpoint confirmation
- [ ] Current branch is recorded.
- [ ] Current HEAD commit is recorded.
- [ ] Working tree is clean before evidence capture starts.
- [ ] Evidence work is being performed against the shipped local artifact-file workflow only.

### 2. Artifact/sample readiness
- [ ] A populated local review artifact example is available.
- [ ] An empty or missing metadata example is available, if practical.
- [ ] Artifact/sample paths are recorded for later traceability.
- [ ] Any launch commands needed for the local UI are recorded.

### 3. Required UI surface evidence
- [ ] `Local Review Runs` list page captured.
- [ ] `Create Local Review Run` section captured.
- [ ] List-page table caption is visible in evidence.
- [ ] `Local Review Run Detail` page captured.
- [ ] `Back to local review runs` link is visible in evidence.
- [ ] `Operator Decision Review` section captured in populated state.
- [ ] `No review metadata` state captured, if available.
- [ ] `Update Decision` form captured.
- [ ] `Save Local Decision` button is visible in evidence.

### 4. Editable workflow evidence
- [ ] A local decision update was exercised, or explicitly skipped and noted.
- [ ] If exercised, the post-update persisted detail state was captured.
- [ ] Any changed local companion metadata/artifact file is identified in notes.

### 5. Evidence package completeness
- [ ] Screenshot filenames are consistent and understandable.
- [ ] Each screenshot is mapped to a required surface/state.
- [ ] Notes exist describing what each screenshot shows.
- [ ] Notes include sample/artifact context so the evidence can be reviewed later.
- [ ] Notes clearly call out any missing evidence items.

### 6. Issue logging / deferrals
- [ ] Any missing capture was documented without changing runtime code.
- [ ] Any observed issue was categorized as one of:
  - [ ] sample data gap
  - [ ] local launch/setup issue
  - [ ] genuine shipped UI issue
- [ ] Any runtime issue was deferred to a separately scoped future phase.

### 7. Final release-readiness conclusion
- [ ] Evidence set demonstrates the shipped local operator UI flow end-to-end.
- [ ] Evidence set reflects only shipped behavior, with no speculative features.
- [ ] Checklist reviewer can determine completeness without re-running the session.
- [ ] The track is ready for final closeout documentation.

## Suggested release note summary format
Use a short summary in the eventual closeout:
- repo checkpoint used
- evidence captured
- any skipped items and why
- whether the editable decision flow was exercised
- whether any real issues were found or deferred

## Deliverable
- A docs-only release-style checklist for the local operator UI evidence pass.

## Exit criteria
- Release-style checklist categories are explicit.
- Required evidence expectations are explicit.
- Deferral handling is explicit.
- Final readiness criteria are explicit.
- No runtime behavior has changed.
