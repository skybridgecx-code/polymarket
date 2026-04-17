# Local Operator UI Evidence Notes

## Repo checkpoint
- Branch used: `phase-26a-local-operator-ui-manual-evidence-pass`
- HEAD commit used before capture: `11d976d`
- Working tree clean before capture: yes

## Artifact/sample context
- Artifact directory/path used: `.tmp/operator-ui-artifacts/operator_runs`
- Generated context bundle used: `.tmp/operator-ui-context-bundle.json`
- Run id used: `theme_ctx_strong.analysis_success_export`
- Populated metadata sample used: `.tmp/operator-ui-artifacts/operator_runs/theme_ctx_strong.analysis_success_export.operator_review.json`
- Empty metadata sample used: same run before companion metadata initialization
- Commands used to launch or exercise the local UI:
  - `.venv/bin/pip install python-multipart`
  - `export FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT="$PWD/.tmp/operator-ui-artifacts/operator_runs"`
  - `.venv/bin/python -m uvicorn future_system.operator_ui.app_entry:create_operator_ui_app --factory --reload`
  - `.venv/bin/python -m future_system.cli.review_artifacts --context-source "$PWD/.tmp/operator-ui-context-bundle.json" --target-directory "$PWD/.tmp/operator-ui-artifacts/operator_runs" --analyst-mode stub --initialize-operator-review`

## Screenshot mapping
- `01-list-page.png`: Local Review Runs list page.
- `02-create-section.png`: Create Local Review Run section.
- `03-detail-page.png`: Local Review Run Detail page before companion review metadata was available.
- `04-populated-review.png`: Populated Operator Decision Review state after companion metadata initialization.
- `05-empty-review.png`: Empty/no-review metadata state before companion metadata initialization.
- `06-update-decision-form.png`: Update Decision form with Save Local Decision visible.
- `07-post-update-state.png`: Post-save state after setting review status to decided and decision to approve.

## Decision update exercised
- Review status changed from `pending` to `decided`.
- Operator decision changed from `none` to `approve`.
- Notes attempted: `Manual evidence pass update.`
- Reviewer attempted: `local-evidence-pass`
- Persisted companion metadata confirmed:
  - `review_status`: `decided`
  - `operator_decision`: `approve`

## Skipped items / gaps
- No required screenshot item skipped.
- The notes/reviewer fields did not persist in the observed companion metadata output; this is recorded as an observation, not fixed in this evidence phase.

## Issues observed
- Initial launch required installing missing local dependency `python-multipart`.
- Initial server was launched without `FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT`, which produced the expected artifacts-root unavailable state.
- One stale server/root mismatch caused `artifact_run_not_found`; resolved by restarting Uvicorn with the artifact run directory as `FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT`.
- No runtime code was changed.

## Final note
- Evidence pass complete: yes
- Editable decision flow exercised: yes
- Ready for final archival / handoff: yes
