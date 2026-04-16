# Phase 25B — Local Operator UI Evidence Inventory

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-25b-local-operator-ui-evidence-inventory`
- Phase: `25B — local operator UI evidence inventory`
- Source checkpoint: `phase-25a-local-operator-ui-evidence-scope-lock`

## Purpose
This phase inventories the exact manual evidence that should be captured for the shipped `future_system` local operator UI workflow. It does not change behavior, templates, tests, or runtime code.

## Boundaries
- Docs-only phase.
- No runtime changes.
- No test changes.
- No changes under `src/polymarket_arb/*`.
- No new workflow behavior.
- No infrastructure, DB, queue, notification, scheduling, or production-trading work.

## Evidence capture goals
- Prove the shipped local operator UI flow is present and manually navigable.
- Capture evidence for the key operator surfaces and important visible states.
- Define a consistent walkthrough order so evidence collection is repeatable.
- Define completion criteria so the evidence set can be reviewed without ambiguity.

## Screens / states to capture

### 1. Local Review Runs list page
Capture:
- Page title: `Local Review Runs`
- Create section: `Create Local Review Run`
- Review runs table with caption visible
- Any visible summary columns/rows that show the shipped list layout

Why:
- Confirms list-page wording, layout, and accessible table structure shipped in 23C/24C.

### 2. Trigger/create section on list page
Capture:
- Create Local Review Run section before submission
- Form controls and helper/error text if present
- Any trigger error block state if reproducible

Why:
- Confirms the shipped create/trigger entry surface and alert treatment.

### 3. Local Review Run detail page
Capture:
- Page title: `Local Review Run Detail`
- Back link: `Back to local review runs`
- Main run metadata/content region
- Operator Decision Review section visible

Why:
- Confirms the detail-page information architecture and wording shipped in 23C/24D.

### 4. Detail page with existing operator review metadata
Capture:
- `Operator Decision Review` section populated
- Existing review fields/values visible
- Companion metadata rendering in a normal populated state

Why:
- Confirms rendered review metadata presence from the shipped operator review workflow.

### 5. Detail page with missing/empty metadata state
Capture:
- Empty-state label: `No review metadata`

Why:
- Confirms the explicit empty review state is present and worded correctly.

### 6. Update Decision form
Capture:
- Section title: `Update Decision`
- Fieldset/legend structure
- Controls with descriptive helper text
- Save button: `Save Local Decision`

Why:
- Confirms the shipped editable decision workflow and accessibility structure.

### 7. Post-update persisted state
Capture:
- Detail page after saving a decision update
- Updated review metadata reflected in the rendered detail state

Why:
- Confirms the editable local companion metadata workflow remains observable end-to-end.

## Non-screenshot evidence artifacts to retain
- Terminal command history used to launch or exercise the local operator UI flow
- Names/paths of local artifact directories used during evidence capture
- Any deterministic sample files used to reach populated or empty states
- A short note describing which screenshots correspond to which required surfaces

## Recommended walkthrough order
1. Prepare or identify a local review artifact set.
2. Open the Local Review Runs list page.
3. Capture the list page baseline state.
4. Capture the Create Local Review Run section.
5. Open a run detail page with populated metadata.
6. Capture the populated Operator Decision Review section.
7. Capture the Update Decision form.
8. Perform a local decision update if needed for evidence.
9. Capture the post-update persisted state.
10. Capture an empty/missing metadata example if available.
11. Confirm the evidence set covers all required shipped surfaces.

## Evidence completeness checklist
- [ ] List page captured with correct page title.
- [ ] Create section captured with correct heading.
- [ ] Table caption visible in list-page evidence.
- [ ] Detail page captured with correct title and back link.
- [ ] Populated Operator Decision Review state captured.
- [ ] Empty `No review metadata` state captured, if available.
- [ ] Update Decision form captured with Save Local Decision button visible.
- [ ] Post-update persisted state captured, if update flow is exercised.
- [ ] Artifact/sample context noted so screenshots are understandable later.
- [ ] Evidence set reflects shipped behavior only, with no speculative features.

## Deliverable
- A docs-only evidence inventory that defines what later manual smoke/evidence capture phases must collect.

## Exit criteria
- Required screens/states are explicitly listed.
- Walkthrough order is explicit.
- Artifact expectations are explicit.
- Evidence completeness checklist is explicit.
- No runtime behavior has changed.
