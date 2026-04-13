"""Deterministic tests for future_system.review_file_writers local output boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.review_exports.models import (
    AnalysisFailureReviewExportPayload,
    AnalysisReviewExportPackage,
    AnalysisSuccessReviewExportPayload,
)
from future_system.review_file_writers.writer import write_review_export_files
from future_system.runtime.models import AnalysisRunFailureStage


def test_write_review_export_files_success_writes_markdown_and_json_files(
    tmp_path: Path,
) -> None:
    export_package = _success_export_package()

    result = write_review_export_files(
        export_package=export_package,
        target_directory=tmp_path,
    )

    assert result.status == "success"
    assert result.export_kind == "analysis_success_export"
    assert result.theme_id == "theme_ctx_strong"
    assert result.failure_stage is None

    markdown_path = Path(result.markdown_file_path)
    json_path = Path(result.json_file_path)

    assert markdown_path.name == "theme_ctx_strong.analysis_success_export.md"
    assert json_path.name == "theme_ctx_strong.analysis_success_export.json"
    assert markdown_path.parent == tmp_path.resolve()
    assert json_path.parent == tmp_path.resolve()

    assert markdown_path.read_text(encoding="utf-8") == export_package.payload.markdown_document
    assert json.loads(json_path.read_text(encoding="utf-8")) == export_package.model_dump(
        mode="json"
    )


@pytest.mark.parametrize(
    ("failure_stage", "run_flags"),
    [
        ("analyst_timeout", ["analysis_dry_run", "analyst_timeout"]),
        ("analyst_transport", ["analysis_dry_run", "analyst_transport_failed"]),
        ("reasoning_parse", ["analysis_dry_run", "reasoning_parse_failed"]),
    ],
)
def test_write_review_export_files_failure_preserves_stage_identity(
    tmp_path: Path,
    failure_stage: AnalysisRunFailureStage,
    run_flags: list[str],
) -> None:
    export_package = _failure_export_package(
        failure_stage=failure_stage,
        run_flags=run_flags,
    )

    result = write_review_export_files(
        export_package=export_package,
        target_directory=tmp_path,
    )

    assert result.status == "failed"
    assert result.export_kind == "analysis_failure_export"
    assert result.theme_id == "theme_ctx_strong"
    assert result.failure_stage == failure_stage

    markdown_path = Path(result.markdown_file_path)
    json_path = Path(result.json_file_path)

    assert (
        markdown_path.name
        == f"theme_ctx_strong.analysis_failure_export.{failure_stage}.md"
    )
    assert json_path.name == f"theme_ctx_strong.analysis_failure_export.{failure_stage}.json"

    markdown_text = markdown_path.read_text(encoding="utf-8")
    assert f"- Failure Stage: `{failure_stage}`" in markdown_text

    json_document = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_document["payload"]["failure_stage"] == failure_stage
    assert json_document["run_flags"] == run_flags
    assert "policy_decision" not in json_document["payload"]["json_payload"]


def test_write_review_export_files_is_deterministic_for_same_input(tmp_path: Path) -> None:
    export_package = _success_export_package()

    result_a = write_review_export_files(
        export_package=export_package,
        target_directory=tmp_path,
    )
    result_b = write_review_export_files(
        export_package=export_package,
        target_directory=tmp_path,
    )

    assert result_a.model_dump(mode="json") == result_b.model_dump(mode="json")
    assert Path(result_a.markdown_file_path).read_text(encoding="utf-8") == Path(
        result_b.markdown_file_path
    ).read_text(encoding="utf-8")
    assert Path(result_a.json_file_path).read_text(encoding="utf-8") == Path(
        result_b.json_file_path
    ).read_text(encoding="utf-8")


def test_write_review_export_files_rejects_invalid_target_directory_inputs(
    tmp_path: Path,
) -> None:
    export_package = _success_export_package()
    missing_directory = tmp_path / "missing-dir"
    not_a_directory = tmp_path / "file.txt"
    not_a_directory.write_text("file target", encoding="utf-8")

    with pytest.raises(ValueError, match="existing directory"):
        write_review_export_files(
            export_package=export_package,
            target_directory=missing_directory,
        )

    with pytest.raises(ValueError, match="must be a directory"):
        write_review_export_files(
            export_package=export_package,
            target_directory=not_a_directory,
        )

    with pytest.raises(ValueError, match="non-empty path string"):
        write_review_export_files(
            export_package=export_package,
            target_directory="   ",
        )


def _success_export_package() -> AnalysisReviewExportPackage:
    payload = AnalysisSuccessReviewExportPayload(
        export_kind="analysis_success_export",
        status="success",
        theme_id="theme_ctx_strong",
        bundle_kind="analysis_success_bundle",
        packet_kind="analysis_success",
        run_flags=[
            "analysis_dry_run",
            "stub_analyst_used",
            "reasoning_parsed",
            "policy_computed",
        ],
        json_payload={
            "theme_id": "theme_ctx_strong",
            "status": "success",
            "bundle_kind": "analysis_success_bundle",
            "packet_kind": "analysis_success",
            "run_flags": [
                "analysis_dry_run",
                "stub_analyst_used",
                "reasoning_parsed",
                "policy_computed",
            ],
            "policy_decision": "candidate",
            "rendered_markdown": "## Review\n- Status: success",
        },
        markdown_document=(
            "# Analysis Review Export\n"
            "- Export Kind: `analysis_success_export`\n"
            "- Status: `success`\n"
            "- Theme ID: `theme_ctx_strong`\n"
            "## Rendered Review\n"
            "## Review\n"
            "- Status: success\n"
        ),
        export_summary=(
            "theme_id=theme_ctx_strong; export_kind=analysis_success_export; "
            "status=success; run_flags=analysis_dry_run,stub_analyst_used,"
            "reasoning_parsed,policy_computed."
        ),
    )
    return AnalysisReviewExportPackage(
        theme_id="theme_ctx_strong",
        status="success",
        export_kind="analysis_success_export",
        run_flags=list(payload.run_flags),
        payload=payload,
    )


def _failure_export_package(
    *,
    failure_stage: AnalysisRunFailureStage,
    run_flags: list[str],
) -> AnalysisReviewExportPackage:
    payload = AnalysisFailureReviewExportPayload(
        export_kind="analysis_failure_export",
        status="failed",
        theme_id="theme_ctx_strong",
        bundle_kind="analysis_failure_bundle",
        packet_kind="analysis_failure",
        failure_stage=failure_stage,
        run_flags=list(run_flags),
        json_payload={
            "theme_id": "theme_ctx_strong",
            "status": "failed",
            "bundle_kind": "analysis_failure_bundle",
            "packet_kind": "analysis_failure",
            "failure_stage": failure_stage,
            "run_flags": list(run_flags),
            "error_message": "simulated deterministic failure",
        },
        markdown_document=(
            "# Analysis Review Export\n"
            "- Export Kind: `analysis_failure_export`\n"
            "- Status: `failed`\n"
            "- Theme ID: `theme_ctx_strong`\n"
            f"- Failure Stage: `{failure_stage}`\n"
            "## Rendered Review\n"
            "- Failure output only.\n"
        ),
        export_summary=(
            "theme_id=theme_ctx_strong; export_kind=analysis_failure_export; "
            "status=failed; "
            f"failure_stage={failure_stage}; "
            f"run_flags={','.join(run_flags)}."
        ),
    )
    return AnalysisReviewExportPackage(
        theme_id="theme_ctx_strong",
        status="failed",
        export_kind="analysis_failure_export",
        run_flags=list(run_flags),
        payload=payload,
    )
