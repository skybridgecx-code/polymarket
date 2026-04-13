"""Builder helpers for deterministic operator review decision metadata contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from future_system.review_exports.models import ReviewExportKind
from future_system.runtime.models import AnalysisRunFailureStage, AnalysisRunStatus

from .models import OperatorReviewArtifactReference, OperatorReviewDecisionRecord


def build_initial_operator_review_decision_record(
    *,
    run_id: str,
    artifact_payload: Mapping[str, object],
    json_file_path: str | None = None,
    markdown_file_path: str | None = None,
) -> OperatorReviewDecisionRecord:
    """Build a default pending review record from one existing export artifact payload."""

    theme_id = _require_string(artifact_payload.get("theme_id"), "artifact_payload.theme_id")
    status = _require_status(artifact_payload.get("status"))
    payload_mapping = _optional_payload_mapping(artifact_payload.get("payload"))
    export_kind = _require_export_kind(
        _resolve_export_kind(
            artifact_payload=artifact_payload,
            payload_mapping=payload_mapping,
        )
    )
    failure_stage = _resolve_failure_stage(
        status=status,
        payload_mapping=payload_mapping,
    )
    run_flags_snapshot = _resolve_run_flags_snapshot(
        artifact_payload=artifact_payload,
        payload_mapping=payload_mapping,
    )
    return OperatorReviewDecisionRecord(
        artifact=OperatorReviewArtifactReference(
            run_id=run_id,
            theme_id=theme_id,
            status=status,
            export_kind=export_kind,
            failure_stage=failure_stage,
            json_file_path=json_file_path,
            markdown_file_path=markdown_file_path,
        ),
        review_status="pending",
        run_flags_snapshot=run_flags_snapshot,
    )


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty.")
    return normalized


def _require_status(value: object) -> AnalysisRunStatus:
    if value == "success":
        return "success"
    if value == "failed":
        return "failed"
    raise ValueError("artifact_payload.status must be 'success' or 'failed'.")


def _optional_payload_mapping(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("artifact_payload.payload keys must be strings.")
            normalized[key] = item
        return normalized
    raise ValueError("artifact_payload.payload must be an object when provided.")


def _resolve_export_kind(
    *,
    artifact_payload: Mapping[str, object],
    payload_mapping: Mapping[str, object],
) -> object:
    top_level = artifact_payload.get("export_kind")
    if top_level is not None:
        return top_level
    return payload_mapping.get("export_kind")


def _require_export_kind(value: object) -> ReviewExportKind:
    if value == "analysis_success_export":
        return "analysis_success_export"
    if value == "analysis_failure_export":
        return "analysis_failure_export"
    raise ValueError(
        "artifact_payload export_kind must be 'analysis_success_export' or "
        "'analysis_failure_export'."
    )


def _resolve_failure_stage(
    *,
    status: AnalysisRunStatus,
    payload_mapping: Mapping[str, object],
) -> AnalysisRunFailureStage | None:
    if status == "success":
        return None

    raw_stage = payload_mapping.get("failure_stage")
    if raw_stage not in {"analyst_timeout", "analyst_transport", "reasoning_parse"}:
        raise ValueError("artifact_payload.payload.failure_stage is required for failed artifacts.")
    return cast(AnalysisRunFailureStage, raw_stage)


def _resolve_run_flags_snapshot(
    *,
    artifact_payload: Mapping[str, object],
    payload_mapping: Mapping[str, object],
) -> list[str]:
    raw = artifact_payload.get("run_flags")
    if raw is None:
        raw = payload_mapping.get("run_flags")
    return _normalize_string_list(raw, "run_flags_snapshot")


def _normalize_string_list(value: object, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings when provided.")

    normalized: list[str] = []
    for item in value:
        token = _require_string(item, field_name)
        if token in normalized:
            continue
        normalized.append(token)
    return normalized


__all__ = ["build_initial_operator_review_decision_record"]
