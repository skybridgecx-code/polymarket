"""Deterministic tests for operator_ui package-level public exports."""

from __future__ import annotations

from future_system import operator_ui
from future_system.operator_ui.app_entry import (
    DEFAULT_OPERATOR_UI_MOUNT_PATH,
    create_operator_ui_app,
    mount_operator_ui_app,
)
from future_system.operator_ui.review_artifacts import (
    TriggerRunResult,
    create_review_artifacts_operator_app,
    discover_review_artifact_history,
    discover_review_artifact_runs,
    read_review_artifact_run_detail,
    trigger_review_artifact_run,
)


def test_operator_ui_package_exports_match_review_artifact_surface() -> None:
    assert operator_ui.DEFAULT_OPERATOR_UI_MOUNT_PATH == DEFAULT_OPERATOR_UI_MOUNT_PATH
    assert operator_ui.create_operator_ui_app is create_operator_ui_app
    assert operator_ui.create_review_artifacts_operator_app is create_review_artifacts_operator_app
    assert operator_ui.create_operator_ui_app is operator_ui.create_review_artifacts_operator_app
    assert operator_ui.mount_operator_ui_app is mount_operator_ui_app
    assert operator_ui.trigger_review_artifact_run is trigger_review_artifact_run
    assert operator_ui.read_review_artifact_run_detail is read_review_artifact_run_detail
    assert operator_ui.discover_review_artifact_history is discover_review_artifact_history
    assert operator_ui.discover_review_artifact_runs is discover_review_artifact_runs
    assert operator_ui.TriggerRunResult is TriggerRunResult
