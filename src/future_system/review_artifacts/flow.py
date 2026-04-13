"""Deterministic bounded composition flow from runtime result to written review artifacts."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from future_system.review_artifacts.models import (
    AnalysisFailureReviewArtifactFlowResult,
    AnalysisReviewArtifactFlowEnvelope,
    AnalysisSuccessReviewArtifactFlowResult,
)
from future_system.review_bundles.builder import build_review_bundle
from future_system.review_exports.builder import build_review_export_payloads
from future_system.review_file_writers.models import (
    AnalysisFailureReviewFileWriteResult,
    AnalysisSuccessReviewFileWriteResult,
)
from future_system.review_file_writers.writer import write_review_export_files
from future_system.runtime.models import AnalysisRunResultEnvelope


def build_and_write_review_artifacts(
    *,
    runtime_result: AnalysisRunResultEnvelope,
    target_directory: str | Path,
) -> AnalysisReviewArtifactFlowEnvelope:
    """Compose bundle/export/file-writer layers to emit deterministic local review artifacts."""

    review_bundle = build_review_bundle(runtime_result=runtime_result)
    export_package = build_review_export_payloads(review_bundle=review_bundle)
    file_write_result = write_review_export_files(
        export_package=export_package,
        target_directory=target_directory,
    )

    if runtime_result.status == "success":
        success_packet = runtime_result.success
        if success_packet is None:
            raise ValueError("review_artifact_flow_missing_success_runtime_packet")
        if not isinstance(file_write_result, AnalysisSuccessReviewFileWriteResult):
            raise ValueError("review_artifact_flow_success_write_result_mismatch")

        return AnalysisReviewArtifactFlowEnvelope(
            status="success",
            flow_result=AnalysisSuccessReviewArtifactFlowResult(
                flow_kind="analysis_success_artifact_flow",
                status="success",
                theme_id=success_packet.theme_id,
                target_directory=file_write_result.target_directory,
                runtime_result=runtime_result,
                review_bundle=review_bundle,
                export_package=export_package,
                file_write_result=file_write_result,
                run_flags=list(success_packet.run_flags),
                flow_summary=_build_success_flow_summary(
                    theme_id=success_packet.theme_id,
                    run_flags=success_packet.run_flags,
                    markdown_file_path=file_write_result.markdown_file_path,
                    json_file_path=file_write_result.json_file_path,
                ),
            ),
        )

    failure_packet = runtime_result.failure
    if failure_packet is None:
        raise ValueError("review_artifact_flow_missing_failure_runtime_packet")
    if not isinstance(file_write_result, AnalysisFailureReviewFileWriteResult):
        raise ValueError("review_artifact_flow_failure_write_result_mismatch")

    return AnalysisReviewArtifactFlowEnvelope(
        status="failed",
        flow_result=AnalysisFailureReviewArtifactFlowResult(
            flow_kind="analysis_failure_artifact_flow",
            status="failed",
            theme_id=failure_packet.theme_id,
            target_directory=file_write_result.target_directory,
            runtime_result=runtime_result,
            review_bundle=review_bundle,
            export_package=export_package,
            file_write_result=file_write_result,
            run_flags=list(failure_packet.run_flags),
            failure_stage=failure_packet.failure_stage,
            flow_summary=_build_failure_flow_summary(
                theme_id=failure_packet.theme_id,
                failure_stage=failure_packet.failure_stage,
                run_flags=failure_packet.run_flags,
                markdown_file_path=file_write_result.markdown_file_path,
                json_file_path=file_write_result.json_file_path,
            ),
        ),
    )


def _build_success_flow_summary(
    *,
    theme_id: str,
    run_flags: Sequence[str],
    markdown_file_path: str,
    json_file_path: str,
) -> str:
    run_flags_text = _run_flags_text(run_flags)
    return (
        f"theme_id={theme_id}; "
        "flow_kind=analysis_success_artifact_flow; "
        "status=success; "
        f"run_flags={run_flags_text}; "
        f"markdown_file={markdown_file_path}; "
        f"json_file={json_file_path}."
    )


def _build_failure_flow_summary(
    *,
    theme_id: str,
    failure_stage: str,
    run_flags: Sequence[str],
    markdown_file_path: str,
    json_file_path: str,
) -> str:
    run_flags_text = _run_flags_text(run_flags)
    return (
        f"theme_id={theme_id}; "
        "flow_kind=analysis_failure_artifact_flow; "
        "status=failed; "
        f"failure_stage={failure_stage}; "
        f"run_flags={run_flags_text}; "
        f"markdown_file={markdown_file_path}; "
        f"json_file={json_file_path}."
    )


def _run_flags_text(run_flags: Sequence[str]) -> str:
    if not run_flags:
        return "none"
    return ",".join(run_flags)
