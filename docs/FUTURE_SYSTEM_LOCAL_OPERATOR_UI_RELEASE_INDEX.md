# Future System Local Operator UI Release Index

## Repo / Checkpoint
- Repo: `polymarket-arb`
- Branch: `phase-30a-operator-ui-launcher-smoke-tests`
- HEAD: `742c1aab47a70cfe499a60b028e96db8c7612272`
- Track covered: shipped local `future_system` operator UI workflow through Phase 30A

## Shipped Workflow Summary
- Local review artifact workflow: CLI creates per-run markdown/json artifacts in a local artifacts directory.
- Optional operator review metadata initialization: CLI `--initialize-operator-review` creates `X.operator_review.json` when absent.
- Local review runs list/detail pages: UI renders run list, run detail, and bounded file issues states.
- Editable decision form: UI exposes local operator review update form for status/decision/notes/reviewer.
- Deterministic local companion metadata rewrite: update flow rewrites only companion metadata under configured artifacts root.
- Local evidence package: screenshots and notes capture list/create/detail/review/edit/post-save states.

## Runbook
- [Future System Operator UI Local Runbook](./FUTURE_SYSTEM_OPERATOR_UI_LOCAL_RUNBOOK.md)
- Runbook refresh status: Phase 33A refreshed the main local E2E runbook; see [PHASE_33A_OPERATOR_UI_E2E_RUNBOOK_REFRESH.md](./PHASE_33A_OPERATOR_UI_E2E_RUNBOOK_REFRESH.md).

## Local Demo Launcher
- Launcher script: [scripts/launch_future_system_operator_ui_demo.sh](../scripts/launch_future_system_operator_ui_demo.sh)
- Launch command: `make future-system-operator-ui-demo`
- Prepare-only command: `make future-system-operator-ui-demo-prepare`
- Port override supported: `PORT=8001 make future-system-operator-ui-demo` (default port is `8000`)
- Cleanup command: `make future-system-operator-ui-demo-clean` (removes only `.tmp/future-system-operator-ui-demo`)
- Validation command: `make future-system-operator-ui-demo-validate`
- Validation hardening status: Phase 34B strengthened launcher validation coverage for non-empty artifacts, metadata content contracts, and bounded `.tmp` cleanup checks; see [PHASE_34B_DEMO_WORKFLOW_VALIDATION_HARDENING.md](./PHASE_34B_DEMO_WORKFLOW_VALIDATION_HARDENING.md).
- Launcher output/failure-message polish status: Phase 34C improved launcher stdout sectioning and failure clarity without behavior changes; see [PHASE_34C_LAUNCHER_OUTPUT_FAILURE_MESSAGE_POLISH.md](./PHASE_34C_LAUNCHER_OUTPUT_FAILURE_MESSAGE_POLISH.md).
- End-to-end smoke checklist status: Phase 34D provides the full demo workflow smoke checklist; see [PHASE_34D_DEMO_WORKFLOW_E2E_SMOKE_CHECKLIST.md](./PHASE_34D_DEMO_WORKFLOW_E2E_SMOKE_CHECKLIST.md).
- Demo launcher status: Phase 29A–29E tooling track is complete; see [PHASE_29E_DEMO_LAUNCHER_TRACK_CLOSEOUT.md](./PHASE_29E_DEMO_LAUNCHER_TRACK_CLOSEOUT.md).
- Run detail UX manual smoke checklist: [PHASE_31D_RUN_DETAIL_UX_MANUAL_SMOKE.md](./PHASE_31D_RUN_DETAIL_UX_MANUAL_SMOKE.md)
- Run detail UX track status: Phase 31A–31E is complete; see [PHASE_31E_RUN_DETAIL_UX_TRACK_CLOSEOUT.md](./PHASE_31E_RUN_DETAIL_UX_TRACK_CLOSEOUT.md).
- List/create UX manual smoke checklist: [PHASE_32D_LIST_CREATE_UX_MANUAL_SMOKE.md](./PHASE_32D_LIST_CREATE_UX_MANUAL_SMOKE.md)
- List/create UX track status: Phase 32A–32E is complete; see [PHASE_32E_LIST_CREATE_UX_TRACK_CLOSEOUT.md](./PHASE_32E_LIST_CREATE_UX_TRACK_CLOSEOUT.md).
- Phase handoff docs:
  - [PHASE_29A_LOCAL_OPERATOR_UI_DEMO_LAUNCHER.md](./PHASE_29A_LOCAL_OPERATOR_UI_DEMO_LAUNCHER.md)
  - [PHASE_29B_DEMO_LAUNCHER_PORT_HANDLING.md](./PHASE_29B_DEMO_LAUNCHER_PORT_HANDLING.md)
  - [PHASE_29C_DEMO_LAUNCHER_CLEANUP_TARGET.md](./PHASE_29C_DEMO_LAUNCHER_CLEANUP_TARGET.md)
  - [PHASE_29D_DEMO_LAUNCHER_PREPARE_ONLY_MODE.md](./PHASE_29D_DEMO_LAUNCHER_PREPARE_ONLY_MODE.md)
  - [PHASE_29E_DEMO_LAUNCHER_TRACK_CLOSEOUT.md](./PHASE_29E_DEMO_LAUNCHER_TRACK_CLOSEOUT.md)
  - [PHASE_30A_OPERATOR_UI_LAUNCHER_SMOKE_TESTS.md](./PHASE_30A_OPERATOR_UI_LAUNCHER_SMOKE_TESTS.md)

## Evidence Package
- Evidence notes: [evidence/local-operator-ui/notes.md](../evidence/local-operator-ui/notes.md)
- Screenshots:
  - [evidence/local-operator-ui/01-list-page.png](../evidence/local-operator-ui/01-list-page.png)
  - [evidence/local-operator-ui/02-create-section.png](../evidence/local-operator-ui/02-create-section.png)
  - [evidence/local-operator-ui/03-detail-page.png](../evidence/local-operator-ui/03-detail-page.png)
  - [evidence/local-operator-ui/04-populated-review.png](../evidence/local-operator-ui/04-populated-review.png)
  - [evidence/local-operator-ui/05-empty-review.png](../evidence/local-operator-ui/05-empty-review.png)
  - [evidence/local-operator-ui/06-update-decision-form.png](../evidence/local-operator-ui/06-update-decision-form.png)
  - [evidence/local-operator-ui/07-post-update-state.png](../evidence/local-operator-ui/07-post-update-state.png)

## Closeout and Audit Docs
- [Phase 20F Decision Workflow Closeout Checkpoint](./PHASE_20F_DECISION_WORKFLOW_CLOSEOUT_CHECKPOINT.md)
- [Phase 21F Editable Decision Workflow Closeout](./PHASE_21F_EDITABLE_DECISION_WORKFLOW_CLOSEOUT.md)
- [Phase 22E Editable Workflow Verification Closeout](./PHASE_22E_EDITABLE_WORKFLOW_VERIFICATION_CLOSEOUT.md)
- [Phase 23F UI Copy UX Closeout](./PHASE_23F_UI_COPY_UX_CLOSEOUT.md)
- [Phase 24F Layout Accessibility Closeout](./PHASE_24F_LAYOUT_ACCESSIBILITY_CLOSEOUT.md)
- [Phase 25F Local Operator UI Evidence Final Checkpoint](./PHASE_25F_LOCAL_OPERATOR_UI_EVIDENCE_FINAL_CHECKPOINT.md)
- [Phase 26B Local Operator UI Evidence Closeout](./PHASE_26B_LOCAL_OPERATOR_UI_EVIDENCE_CLOSEOUT.md)
- [Phase 27A Operator Review Notes Reviewer Persistence Audit](./PHASE_27A_OPERATOR_REVIEW_NOTES_REVIEWER_PERSISTENCE_AUDIT.md)

## Hard Boundaries
- Local artifact-file workflow only.
- No production trading or execution behavior.
- No DB, queue, background jobs, scheduler, inbox, or notification behavior.
- No `src/polymarket_arb/*` changes in this track.

## Validation Baseline
```bash
pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
ruff check src/future_system/operator_ui tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
mypy src/future_system/operator_ui
```

## Known Observations
- `python-multipart` was needed locally for manual Uvicorn form handling.
- Artifacts root must point at the directory containing run artifacts.
- Notes/reviewer persistence observation was audited in Phase 27A and was not confirmed as a runtime bug.

## Exact Next Recommended Step
- No more UI evidence planning docs are needed for this completed local operator UI track.
- Open a separate runtime/product phase only if there is a specific new operator workflow requirement.

## Demo workflow reliability track status
Phase 34A–34E is complete for the `future_system` local operator UI demo workflow reliability track.

See:
- `docs/PHASE_34E_DEMO_WORKFLOW_RELIABILITY_TRACK_CLOSEOUT.md`

