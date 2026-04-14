"""Deterministic helper for writing initialized operator review companion metadata files."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path

from future_system.operator_review_models import (
    OperatorReviewDecisionRecord,
    build_initial_operator_review_decision_record,
)

_OPERATOR_REVIEW_COMPANION_SUFFIX = ".operator_review.json"
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def write_initialized_operator_review_metadata_companion(
    *,
    target_directory: str | Path,
    run_id: str,
    artifact_payload: Mapping[str, object],
    json_file_path: str | None = None,
    markdown_file_path: str | None = None,
) -> str:
    """Write one pending review metadata companion file for an existing artifact payload."""

    resolved_target_directory = _normalize_target_directory(target_directory)
    normalized_run_id = _normalize_run_id(run_id)
    output_path = _bounded_output_path(
        target_directory=resolved_target_directory,
        filename=f"{normalized_run_id}{_OPERATOR_REVIEW_COMPANION_SUFFIX}",
    )
    if output_path.exists():
        raise ValueError(
            "operator_review_metadata_file_exists: refusing to overwrite existing companion file."
        )

    review_record = build_initial_operator_review_decision_record(
        run_id=normalized_run_id,
        artifact_payload=artifact_payload,
        json_file_path=json_file_path,
        markdown_file_path=markdown_file_path,
    )
    output_path.write_text(_render_review_record_json(review_record), encoding="utf-8")
    return str(output_path)


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


def _bounded_output_path(*, target_directory: Path, filename: str) -> Path:
    output_path = (target_directory / filename).resolve()
    try:
        output_path.relative_to(target_directory)
    except ValueError as exc:
        raise ValueError("operator_review_metadata_path_out_of_bounds") from exc
    return output_path


def _render_review_record_json(review_record: OperatorReviewDecisionRecord) -> str:
    return (
        json.dumps(
            review_record.model_dump(mode="json"),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


__all__ = ["write_initialized_operator_review_metadata_companion"]
