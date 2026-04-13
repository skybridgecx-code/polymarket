"""Bounded artifact file read/discovery helpers for operator UI."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, field_validator

from future_system.runtime.models import AnalysisRunFailureStage

from .root_status import resolve_artifacts_root

_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class ArtifactRunListItem(BaseModel):
    """One bounded list-row record for a discovered artifact run."""

    run_id: str
    theme_id: str
    status: Literal["success", "failed"]
    failure_stage: AnalysisRunFailureStage | None = None
    status_label: str
    updated_at_epoch_ns: int
    updated_at_label: str
    markdown_path: str
    json_path: str

    @field_validator(
        "run_id",
        "theme_id",
        "status_label",
        "updated_at_label",
        "markdown_path",
        "json_path",
        mode="before",
    )
    @classmethod
    def _normalize_text_fields(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("artifact list fields must be strings.")
        normalized = value.strip()
        if not normalized:
            raise ValueError("artifact list fields must be non-empty strings.")
        return normalized

    @field_validator("updated_at_epoch_ns", mode="before")
    @classmethod
    def _validate_updated_at_epoch_ns(cls, value: Any) -> int:
        if not isinstance(value, int):
            raise ValueError("updated_at_epoch_ns must be an integer.")
        if value < 0:
            raise ValueError("updated_at_epoch_ns must be non-negative.")
        return value


class ArtifactRunIssue(BaseModel):
    """One explicit safe issue found while reading artifact run files."""

    run_id: str
    issue_kind: Literal[
        "invalid_run_id",
        "json_invalid",
        "json_fields_invalid",
        "markdown_missing",
    ]
    issue_message: str
    json_path: str
    markdown_path: str

    @field_validator("run_id", "issue_message", "json_path", "markdown_path", mode="before")
    @classmethod
    def _normalize_issue_text_fields(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("artifact issue fields must be strings.")
        normalized = value.strip()
        if not normalized:
            raise ValueError("artifact issue fields must be non-empty strings.")
        return normalized


class ArtifactRunHistory(BaseModel):
    """Bounded run history view with valid runs and explicit file-read issues."""

    runs: list[ArtifactRunListItem]
    issues: list[ArtifactRunIssue]


class ArtifactRunDetail(BaseModel):
    """Bounded detail payload for one run used by the operator UI."""

    run: ArtifactRunListItem
    markdown_content: str
    json_content: dict[str, object]


def discover_review_artifact_runs(*, artifacts_root: Path) -> list[ArtifactRunListItem]:
    """Enumerate deterministic valid run list records from bounded artifact files."""

    return discover_review_artifact_history(artifacts_root=artifacts_root).runs


def discover_review_artifact_history(*, artifacts_root: Path) -> ArtifactRunHistory:
    """Enumerate deterministic run history with explicit safe file-read issues."""

    root = resolve_artifacts_root(artifacts_root)
    runs: list[ArtifactRunListItem] = []
    issues: list[ArtifactRunIssue] = []

    json_paths = sorted(
        root.glob("*.json"),
        key=lambda path: (-path.stat().st_mtime_ns, path.name),
    )

    for json_path in json_paths:
        run_id = json_path.stem
        markdown_path = root / f"{run_id}.md"
        if not _RUN_ID_PATTERN.fullmatch(run_id):
            issues.append(
                ArtifactRunIssue(
                    run_id=run_id,
                    issue_kind="invalid_run_id",
                    issue_message="run_id contains invalid characters.",
                    json_path=str(json_path),
                    markdown_path=str(markdown_path),
                )
            )
            continue
        try:
            payload = _read_export_json(json_path=json_path)
        except ValueError as exc:
            issues.append(
                ArtifactRunIssue(
                    run_id=run_id,
                    issue_kind="json_invalid",
                    issue_message=str(exc),
                    json_path=str(json_path),
                    markdown_path=str(markdown_path),
                )
            )
            continue

        try:
            theme_id = _require_string(payload.get("theme_id"), "theme_id")
            status = _require_status(payload.get("status"))
            failure_stage = _optional_failure_stage(payload)
        except ValueError as exc:
            issues.append(
                ArtifactRunIssue(
                    run_id=run_id,
                    issue_kind="json_fields_invalid",
                    issue_message=str(exc),
                    json_path=str(json_path),
                    markdown_path=str(markdown_path),
                )
            )
            continue

        if not markdown_path.exists() or not markdown_path.is_file():
            issues.append(
                ArtifactRunIssue(
                    run_id=run_id,
                    issue_kind="markdown_missing",
                    issue_message="artifact_markdown_missing: markdown file is missing.",
                    json_path=str(json_path),
                    markdown_path=str(markdown_path),
                )
            )

        run_status_label = status_label(status=status, failure_stage=failure_stage)
        updated_at_epoch_ns = json_path.stat().st_mtime_ns
        runs.append(
            ArtifactRunListItem(
                run_id=run_id,
                theme_id=theme_id,
                status=status,
                failure_stage=failure_stage,
                status_label=run_status_label,
                updated_at_epoch_ns=updated_at_epoch_ns,
                updated_at_label=_format_timestamp_ns(updated_at_epoch_ns),
                markdown_path=str(markdown_path),
                json_path=str(json_path),
            )
        )

    return ArtifactRunHistory(runs=runs, issues=issues)


def read_review_artifact_run_detail(*, artifacts_root: Path, run_id: str) -> ArtifactRunDetail:
    """Read one run detail strictly from files under the configured artifacts root."""

    root = resolve_artifacts_root(artifacts_root)
    normalized_run_id = normalize_run_id(run_id)

    json_path = _bounded_run_path(root=root, run_id=normalized_run_id, suffix=".json")
    markdown_path = _bounded_run_path(root=root, run_id=normalized_run_id, suffix=".md")

    if not json_path.exists() or not json_path.is_file():
        raise ValueError("artifact_run_not_found: json file is missing.")
    if not markdown_path.exists() or not markdown_path.is_file():
        raise ValueError("artifact_markdown_missing: markdown file is missing.")

    payload = _read_export_json(json_path=json_path)
    status = _require_status(payload.get("status"))
    failure_stage = _optional_failure_stage(payload)
    updated_at_epoch_ns = json_path.stat().st_mtime_ns
    run = ArtifactRunListItem(
        run_id=normalized_run_id,
        theme_id=_require_string(payload.get("theme_id"), "theme_id"),
        status=status,
        failure_stage=failure_stage,
        status_label=status_label(status=status, failure_stage=failure_stage),
        updated_at_epoch_ns=updated_at_epoch_ns,
        updated_at_label=_format_timestamp_ns(updated_at_epoch_ns),
        markdown_path=str(markdown_path),
        json_path=str(json_path),
    )

    markdown_content = markdown_path.read_text(encoding="utf-8")
    return ArtifactRunDetail(
        run=run,
        markdown_content=markdown_content,
        json_content=payload,
    )


def normalize_run_id(run_id: str) -> str:
    """Normalize and validate one run id used in bounded artifact file naming."""

    normalized = run_id.strip()
    if not normalized:
        raise ValueError("artifact_run_id_invalid: run_id must be a non-empty string.")
    if not _RUN_ID_PATTERN.fullmatch(normalized):
        raise ValueError("artifact_run_id_invalid: run_id contains invalid characters.")
    return normalized


def status_label(
    *,
    status: Literal["success", "failed"],
    failure_stage: AnalysisRunFailureStage | None,
) -> str:
    """Render one deterministic status label for list/detail surfaces."""

    if status == "success":
        return "SUCCESS"
    if failure_stage is None:
        return "FAILED"
    return f"FAILED ({failure_stage})"


def _bounded_run_path(*, root: Path, run_id: str, suffix: str) -> Path:
    path = (root / f"{run_id}{suffix}").resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("artifact_run_path_out_of_bounds") from exc
    return path


def _read_export_json(*, json_path: Path) -> dict[str, object]:
    try:
        parsed = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("artifact_json_invalid: malformed JSON content.") from exc
    if not isinstance(parsed, dict):
        raise ValueError("artifact_json_invalid: top-level artifact payload must be an object.")
    normalized: dict[str, object] = {}
    for key, value in parsed.items():
        if not isinstance(key, str):
            raise ValueError("artifact_json_invalid: object keys must be strings.")
        normalized[key] = value
    return normalized


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"artifact_json_invalid: {field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"artifact_json_invalid: {field_name} must be non-empty.")
    return normalized


def _require_status(value: object) -> Literal["success", "failed"]:
    if value == "success":
        return "success"
    if value == "failed":
        return "failed"
    raise ValueError("artifact_json_invalid: status must be 'success' or 'failed'.")


def _optional_failure_stage(payload: dict[str, object]) -> AnalysisRunFailureStage | None:
    if payload.get("status") != "failed":
        return None

    payload_field = payload.get("payload")
    if not isinstance(payload_field, dict):
        raise ValueError("artifact_json_invalid: payload must be an object.")
    failure_stage = payload_field.get("failure_stage")
    if failure_stage not in {"analyst_timeout", "analyst_transport", "reasoning_parse"}:
        raise ValueError("artifact_json_invalid: failure_stage is invalid for failed runs.")
    if not isinstance(failure_stage, str):
        raise ValueError("artifact_json_invalid: failure_stage must be a string.")
    return cast(AnalysisRunFailureStage, failure_stage)


def _format_timestamp_ns(timestamp_ns: int) -> str:
    timestamp_seconds = timestamp_ns / 1_000_000_000
    formatted = datetime.fromtimestamp(timestamp_seconds, tz=UTC)
    return formatted.isoformat(timespec="seconds")


__all__ = [
    "ArtifactRunDetail",
    "ArtifactRunHistory",
    "ArtifactRunIssue",
    "ArtifactRunListItem",
    "discover_review_artifact_history",
    "discover_review_artifact_runs",
    "normalize_run_id",
    "read_review_artifact_run_detail",
    "status_label",
]
