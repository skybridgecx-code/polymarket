"""Deterministic tests for operator UI app wiring/config assembly helpers."""

from __future__ import annotations

from pathlib import Path

from future_system.operator_ui.app_wiring import (
    DEFAULT_TRIGGER_ANALYST_MODE_CHOICES,
    DEFAULT_TRIGGER_TARGET_SUBDIRECTORY,
    build_review_artifacts_operator_ui_assembly,
    build_review_artifacts_operator_ui_config,
)
from future_system.operator_ui.artifact_reads import ArtifactRunDetail, ArtifactRunHistory


def test_build_review_artifacts_operator_ui_config_defaults() -> None:
    config = build_review_artifacts_operator_ui_config()

    assert config.trigger_analyst_mode_choices == DEFAULT_TRIGGER_ANALYST_MODE_CHOICES
    assert config.default_trigger_analyst_mode == "stub"
    assert config.default_trigger_context_source == ""
    assert config.default_target_subdirectory == DEFAULT_TRIGGER_TARGET_SUBDIRECTORY


def test_build_review_artifacts_operator_ui_assembly_wires_root_status_and_dependencies(
    tmp_path: Path,
) -> None:
    assembly = build_review_artifacts_operator_ui_assembly(
        artifacts_root=tmp_path,
        discover_review_artifact_history_fn=_discover_history_stub,
        trigger_review_artifact_run_fn=_trigger_run_stub,
        read_review_artifact_run_detail_fn=_read_detail_stub,
        resolve_target_subdirectory_fn=_resolve_subdirectory_stub,
    )

    assert assembly.root_status.state == "configured_readable"
    assert assembly.root_status.is_usable is True
    assert assembly.root_status.resolved_root == tmp_path.resolve()
    assert assembly.dependencies.discover_review_artifact_history_fn is _discover_history_stub
    assert assembly.dependencies.trigger_review_artifact_run_fn is _trigger_run_stub
    assert assembly.dependencies.read_review_artifact_run_detail_fn is _read_detail_stub
    assert assembly.dependencies.resolve_target_subdirectory_fn is _resolve_subdirectory_stub
    assert assembly.config.default_target_subdirectory == DEFAULT_TRIGGER_TARGET_SUBDIRECTORY


def test_build_review_artifacts_operator_ui_assembly_preserves_missing_root_state(
    tmp_path: Path,
) -> None:
    missing_root = tmp_path / "missing-root"
    assembly = build_review_artifacts_operator_ui_assembly(
        artifacts_root=missing_root,
        discover_review_artifact_history_fn=_discover_history_stub,
        trigger_review_artifact_run_fn=_trigger_run_stub,
        read_review_artifact_run_detail_fn=_read_detail_stub,
        resolve_target_subdirectory_fn=_resolve_subdirectory_stub,
    )

    assert assembly.root_status.state == "configured_missing"
    assert assembly.root_status.is_usable is False
    assert assembly.root_status.resolved_root is None


def _discover_history_stub(*, artifacts_root: Path) -> ArtifactRunHistory:
    del artifacts_root
    return ArtifactRunHistory(runs=[], issues=[])


def _trigger_run_stub(
    *,
    artifacts_root: Path,
    context_source: str,
    analyst_mode: str = "stub",
    target_subdirectory: str = DEFAULT_TRIGGER_TARGET_SUBDIRECTORY,
) -> object:
    del artifacts_root, context_source, analyst_mode, target_subdirectory
    return object()


def _read_detail_stub(*, artifacts_root: Path, run_id: str) -> ArtifactRunDetail:
    del artifacts_root, run_id
    raise AssertionError("read-detail stub should not be called in wiring tests.")


def _resolve_subdirectory_stub(
    *,
    artifacts_root: Path,
    target_subdirectory: str,
    create: bool,
) -> tuple[Path, str]:
    del create
    return artifacts_root, target_subdirectory
