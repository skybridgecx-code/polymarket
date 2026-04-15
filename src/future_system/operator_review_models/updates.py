"""Deterministic helper contracts for updating existing operator review metadata files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

from .models import (
    OperatorReviewDecision,
    OperatorReviewDecisionRecord,
    OperatorReviewStatus,
)

_OPERATOR_REVIEW_COMPANION_SUFFIX = ".operator_review.json"
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class OperatorReviewDecisionUpdateInput(BaseModel):
    """Bounded editable-field-only input contract for operator review metadata updates."""

    review_status: OperatorReviewStatus
    operator_decision: OperatorReviewDecision | None = None
    review_notes_summary: str | None = None
    reviewer_identity: str | None = None
    updated_at_epoch_ns: int

    @field_validator("review_notes_summary", "reviewer_identity", mode="before")
    @classmethod
    def _normalize_optional_text_fields(cls, value: Any, info: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{info.field_name} must be a string when provided.")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{info.field_name} must be a non-empty string when provided.")
        return normalized

    @field_validator("updated_at_epoch_ns", mode="before")
    @classmethod
    def _normalize_updated_timestamp(cls, value: Any) -> int:
        if not isinstance(value, int):
            raise ValueError("updated_at_epoch_ns must be an integer.")
        if value < 0:
            raise ValueError("updated_at_epoch_ns must be non-negative.")
        return value


def apply_operator_review_decision_update(
    *,
    existing_record: OperatorReviewDecisionRecord,
    update_input: OperatorReviewDecisionUpdateInput,
) -> OperatorReviewDecisionRecord:
    """Apply one bounded editable-field update while preserving system-owned metadata fields."""

    if update_input.review_status == "pending":
        operator_decision: OperatorReviewDecision | None = None
        decided_at_epoch_ns: int | None = None
    else:
        operator_decision = update_input.operator_decision
        if operator_decision is None:
            raise ValueError(
                "operator_decision is required when review_status is set to 'decided'."
            )
        decided_at_epoch_ns = existing_record.decided_at_epoch_ns
        if decided_at_epoch_ns is None:
            decided_at_epoch_ns = update_input.updated_at_epoch_ns

    return OperatorReviewDecisionRecord(
        record_kind=existing_record.record_kind,
        record_version=existing_record.record_version,
        artifact=existing_record.artifact.model_copy(deep=True),
        review_status=update_input.review_status,
        operator_decision=operator_decision,
        review_notes_summary=update_input.review_notes_summary,
        reviewer_identity=update_input.reviewer_identity,
        decided_at_epoch_ns=decided_at_epoch_ns,
        updated_at_epoch_ns=update_input.updated_at_epoch_ns,
        run_flags_snapshot=list(existing_record.run_flags_snapshot),
    )


def update_existing_operator_review_metadata_companion(
    *,
    target_directory: str | Path,
    run_id: str,
    update_input: OperatorReviewDecisionUpdateInput,
) -> OperatorReviewDecisionRecord:
    """Read, validate, update, and deterministically rewrite one companion metadata file."""

    resolved_target_directory = _normalize_target_directory(target_directory)
    normalized_run_id = _normalize_run_id(run_id)
    companion_path = _bounded_companion_path(
        target_directory=resolved_target_directory,
        run_id=normalized_run_id,
    )

    if not companion_path.exists():
        raise ValueError(
            "operator_review_metadata_missing: companion metadata file does not exist."
        )
    if not companion_path.is_file():
        raise ValueError(
            "operator_review_metadata_invalid_target: companion path must be a regular file."
        )

    existing_record = _read_existing_record(companion_path=companion_path)
    if existing_record.artifact.run_id != normalized_run_id:
        raise ValueError(
            "operator_review_metadata_invalid: artifact.run_id does not match companion run id."
        )

    updated_record = apply_operator_review_decision_update(
        existing_record=existing_record,
        update_input=update_input,
    )
    companion_path.write_text(
        render_operator_review_decision_record_json(updated_record),
        encoding="utf-8",
    )
    return updated_record


def render_operator_review_decision_record_json(
    record: OperatorReviewDecisionRecord,
) -> str:
    """Render one operator review metadata record as deterministic JSON content."""

    return (
        json.dumps(
            record.model_dump(mode="json"),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def _normalize_target_directory(target_directory: str | Path) -> Path:
    if isinstance(target_directory, Path):
        candidate = target_directory
    elif isinstance(target_directory, str):
        stripped = target_directory.strip()
        if not stripped:
            raise ValueError("target_directory must be a non-empty path string.")
        candidate = Path(stripped)
    else:
        raise ValueError("target_directory must be a path-like string or Path.")

    if not candidate.exists():
        raise ValueError("target_directory must reference an existing directory.")
    if not candidate.is_dir():
        raise ValueError("target_directory must be a directory.")

    return candidate.resolve()


def _normalize_run_id(run_id: str) -> str:
    normalized = run_id.strip()
    if not normalized:
        raise ValueError("run_id must be a non-empty string.")
    if not _RUN_ID_PATTERN.fullmatch(normalized):
        raise ValueError("run_id contains invalid characters.")
    return normalized


def _bounded_companion_path(*, target_directory: Path, run_id: str) -> Path:
    companion_path = (target_directory / f"{run_id}{_OPERATOR_REVIEW_COMPANION_SUFFIX}").resolve()
    try:
        companion_path.relative_to(target_directory)
    except ValueError as exc:
        raise ValueError("operator_review_metadata_update_path_out_of_bounds") from exc
    return companion_path


def _read_existing_record(*, companion_path: Path) -> OperatorReviewDecisionRecord:
    try:
        raw_payload = json.loads(companion_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            "operator_review_metadata_invalid: malformed JSON content."
        ) from exc
    if not isinstance(raw_payload, dict):
        raise ValueError(
            "operator_review_metadata_invalid: top-level metadata payload must be an object."
        )

    try:
        return OperatorReviewDecisionRecord.model_validate(raw_payload)
    except ValidationError as exc:
        raise ValueError(f"operator_review_metadata_invalid: {exc}") from exc


__all__ = [
    "OperatorReviewDecisionUpdateInput",
    "apply_operator_review_decision_update",
    "render_operator_review_decision_record_json",
    "update_existing_operator_review_metadata_companion",
]
