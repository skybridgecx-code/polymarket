"""Deterministic local writer boundary for review export payload packages."""

from __future__ import annotations

import json
import re
from pathlib import Path

from future_system.review_exports.models import (
    AnalysisFailureReviewExportPayload,
    AnalysisReviewExportPackage,
    AnalysisSuccessReviewExportPayload,
)
from future_system.review_file_writers.models import (
    AnalysisFailureReviewFileWriteResult,
    AnalysisReviewFileWriteResult,
    AnalysisSuccessReviewFileWriteResult,
)

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def write_review_export_files(
    *,
    export_package: AnalysisReviewExportPackage,
    target_directory: str | Path,
) -> AnalysisReviewFileWriteResult:
    """Write deterministic markdown/json files from one review export payload package."""

    resolved_target_directory = _normalize_target_directory(target_directory)
    file_stem = _deterministic_file_stem(export_package)

    markdown_path = _bounded_output_path(
        target_directory=resolved_target_directory,
        filename=f"{file_stem}.md",
    )
    json_path = _bounded_output_path(
        target_directory=resolved_target_directory,
        filename=f"{file_stem}.json",
    )

    markdown_bytes_written = _write_utf8_file(
        path=markdown_path,
        content=export_package.payload.markdown_document,
    )
    json_bytes_written = _write_utf8_file(
        path=json_path,
        content=_render_export_json_document(export_package),
    )

    payload = export_package.payload
    if export_package.status == "success":
        if not isinstance(payload, AnalysisSuccessReviewExportPayload):
            raise ValueError("review_file_writer_success_payload_mismatch")
        return AnalysisSuccessReviewFileWriteResult(
            target_directory=str(resolved_target_directory),
            theme_id=export_package.theme_id,
            status=export_package.status,
            export_kind="analysis_success_export",
            markdown_file_path=str(markdown_path),
            json_file_path=str(json_path),
            markdown_bytes_written=markdown_bytes_written,
            json_bytes_written=json_bytes_written,
        )

    if not isinstance(payload, AnalysisFailureReviewExportPayload):
        raise ValueError("review_file_writer_failure_payload_mismatch")

    return AnalysisFailureReviewFileWriteResult(
        target_directory=str(resolved_target_directory),
        theme_id=export_package.theme_id,
        status=export_package.status,
        export_kind="analysis_failure_export",
        failure_stage=payload.failure_stage,
        markdown_file_path=str(markdown_path),
        json_file_path=str(json_path),
        markdown_bytes_written=markdown_bytes_written,
        json_bytes_written=json_bytes_written,
    )


def _render_export_json_document(export_package: AnalysisReviewExportPackage) -> str:
    payload = export_package.model_dump(mode="json")
    if payload.get("cryp_external_confirmation_signal") is None:
        payload.pop("cryp_external_confirmation_signal", None)

    return (
        json.dumps(
            payload,
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


def _deterministic_file_stem(export_package: AnalysisReviewExportPackage) -> str:
    theme_component = _sanitize_filename_component(export_package.theme_id, "theme_id")
    if export_package.status == "success":
        return f"{theme_component}.analysis_success_export"

    payload = export_package.payload
    if not isinstance(payload, AnalysisFailureReviewExportPayload):
        raise ValueError("review_file_writer_failure_payload_mismatch")

    failure_stage_component = _sanitize_filename_component(
        payload.failure_stage,
        "failure_stage",
    )
    return f"{theme_component}.analysis_failure_export.{failure_stage_component}"


def _sanitize_filename_component(value: str, field_name: str) -> str:
    normalized = _UNSAFE_FILENAME_CHARS.sub("_", value.strip()).strip("._")
    if not normalized:
        raise ValueError(f"{field_name} produced an empty filename component.")
    return normalized


def _bounded_output_path(*, target_directory: Path, filename: str) -> Path:
    output_path = (target_directory / filename).resolve()
    try:
        output_path.relative_to(target_directory)
    except ValueError as exc:
        raise ValueError("output path escaped target_directory bounds.") from exc
    return output_path


def _write_utf8_file(*, path: Path, content: str) -> int:
    encoded = content.encode("utf-8")
    path.write_bytes(encoded)
    return len(encoded)
