"""Deterministic top-level entrypoint from runtime entry to written review artifacts."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.review_artifacts.flow import build_and_write_review_artifacts
from future_system.review_entrypoints.models import (
    AnalysisFailureReviewEntryResult,
    AnalysisReviewEntryEnvelope,
    AnalysisSuccessReviewEntryResult,
)
from future_system.runtime.protocol import AnalystProtocol
from future_system.runtime.runner import run_analysis_pipeline_result


def run_analysis_and_write_review_artifacts(
    *,
    context_bundle: OpportunityContextBundle,
    analyst: AnalystProtocol,
    target_directory: str | Path,
    initialize_operator_review: bool = False,
) -> AnalysisReviewEntryEnvelope:
    """Run runtime result entrypoint and compose the downstream review artifact flow."""

    runtime_result = run_analysis_pipeline_result(
        context_bundle=context_bundle,
        analyst=analyst,
    )
    artifact_flow = build_and_write_review_artifacts(
        runtime_result=runtime_result,
        target_directory=target_directory,
        initialize_operator_review=initialize_operator_review,
    )

    if runtime_result.status == "success":
        success_packet = runtime_result.success
        if success_packet is None:
            raise ValueError("review_entrypoint_missing_success_runtime_packet")

        flow_result = artifact_flow.flow_result
        return AnalysisReviewEntryEnvelope(
            status="success",
            entry_result=AnalysisSuccessReviewEntryResult(
                entry_kind="analysis_success_review_entry",
                status="success",
                theme_id=success_packet.theme_id,
                target_directory=flow_result.target_directory,
                runtime_result=runtime_result,
                artifact_flow=artifact_flow,
                run_flags=list(success_packet.run_flags),
                entry_summary=_build_success_entry_summary(
                    theme_id=success_packet.theme_id,
                    run_flags=success_packet.run_flags,
                    markdown_file_path=flow_result.file_write_result.markdown_file_path,
                    json_file_path=flow_result.file_write_result.json_file_path,
                ),
            ),
        )

    failure_packet = runtime_result.failure
    if failure_packet is None:
        raise ValueError("review_entrypoint_missing_failure_runtime_packet")

    flow_result = artifact_flow.flow_result
    return AnalysisReviewEntryEnvelope(
        status="failed",
        entry_result=AnalysisFailureReviewEntryResult(
            entry_kind="analysis_failure_review_entry",
            status="failed",
            theme_id=failure_packet.theme_id,
            target_directory=flow_result.target_directory,
            runtime_result=runtime_result,
            artifact_flow=artifact_flow,
            run_flags=list(failure_packet.run_flags),
            failure_stage=failure_packet.failure_stage,
            entry_summary=_build_failure_entry_summary(
                theme_id=failure_packet.theme_id,
                failure_stage=failure_packet.failure_stage,
                run_flags=failure_packet.run_flags,
                markdown_file_path=flow_result.file_write_result.markdown_file_path,
                json_file_path=flow_result.file_write_result.json_file_path,
            ),
        ),
    )


def _build_success_entry_summary(
    *,
    theme_id: str,
    run_flags: Sequence[str],
    markdown_file_path: str,
    json_file_path: str,
) -> str:
    run_flags_text = _run_flags_text(run_flags)
    return (
        f"theme_id={theme_id}; "
        "entry_kind=analysis_success_review_entry; "
        "status=success; "
        f"run_flags={run_flags_text}; "
        f"markdown_file={markdown_file_path}; "
        f"json_file={json_file_path}."
    )


def _build_failure_entry_summary(
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
        "entry_kind=analysis_failure_review_entry; "
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
