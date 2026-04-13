"""FastAPI operator UI for listing, triggering, and inspecting review artifact runs."""

from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import quote

from fastapi import FastAPI, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, field_validator

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.live_analyst.errors import LiveAnalystTimeoutError, LiveAnalystTransportError
from future_system.reasoning_contracts.models import ReasoningInputPacket, RenderedPromptPacket
from future_system.review_entrypoints.entry import run_analysis_and_write_review_artifacts
from future_system.runtime.models import AnalysisRunFailureStage
from future_system.runtime.protocol import AnalystProtocol, AnalystResponsePayload
from future_system.runtime.stub_analyst import DeterministicStubAnalyst

_ARTIFACTS_ROOT_ENV = "FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT"
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_TRIGGER_ANALYST_MODE_CHOICES = (
    "stub",
    "analyst_timeout",
    "analyst_transport",
    "reasoning_parse",
)
_DETAIL_MARKDOWN_MAX_CHARS = 16_000
_DETAIL_JSON_MAX_CHARS = 24_000
_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY = "operator_runs"
_TARGET_SUBDIRECTORY_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_FAILURE_STAGE_DESCRIPTIONS: dict[AnalysisRunFailureStage, str] = {
    "analyst_timeout": "Analyst timed out before producing a complete response.",
    "analyst_transport": "Analyst transport call failed before a usable response was returned.",
    "reasoning_parse": "Analyst response was received but reasoning payload parsing failed.",
}


@dataclass(frozen=True)
class ArtifactsRootStatus:
    """Bounded status for configured artifacts root visibility and safety checks."""

    state: Literal[
        "configured_readable",
        "configured_missing",
        "configured_invalid_or_unreadable",
        "not_configured",
    ]
    configured_value: str | None
    resolved_root: Path | None
    message: str

    @property
    def is_usable(self) -> bool:
        return self.state == "configured_readable" and self.resolved_root is not None


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


@dataclass(frozen=True)
class TriggerRunResult:
    """Bounded trigger outcome metadata needed for deterministic UI handoff."""

    run_id: str
    target_subdirectory: str


def create_review_artifacts_operator_app(
    *,
    artifacts_root: str | Path | None = None,
) -> FastAPI:
    """Create a bounded read-only operator UI app scoped to one artifacts root."""

    root_status = _resolve_artifacts_root_status(artifacts_root)
    app = FastAPI(title="Future System Review Artifact Operator UI", version="0.1.0")
    app.state.artifacts_root_status = root_status

    @app.get("/", response_class=HTMLResponse)
    async def list_runs() -> str:
        history = _discover_history_for_root_status(root_status=root_status)
        return _render_list_page(
            history=history,
            root_status=root_status,
            trigger_error=None,
            last_context_source="",
            last_analyst_mode="stub",
            last_target_subdirectory=_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY,
        )

    @app.post("/runs/trigger")
    async def trigger_run(
        context_source: str = Form(...),
        analyst_mode: str = Form("stub"),
        target_subdirectory: str = Form(_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY),
    ) -> Response:
        if not root_status.is_usable or root_status.resolved_root is None:
            history = _discover_history_for_root_status(root_status=root_status)
            return HTMLResponse(
                content=_render_list_page(
                    history=history,
                    root_status=root_status,
                    trigger_error=(
                        "artifacts_root_unavailable: "
                        f"{_artifacts_root_unavailable_message(root_status=root_status)}"
                    ),
                    last_context_source=context_source,
                    last_analyst_mode=analyst_mode,
                    last_target_subdirectory=target_subdirectory,
                ),
                status_code=422,
            )

        try:
            run_result = trigger_review_artifact_run(
                artifacts_root=root_status.resolved_root,
                context_source=context_source,
                analyst_mode=analyst_mode,
                target_subdirectory=target_subdirectory,
            )
        except ValueError as exc:
            history = _discover_history_for_root_status(root_status=root_status)
            return HTMLResponse(
                content=_render_list_page(
                    history=history,
                    root_status=root_status,
                    trigger_error=f"Invalid trigger input: {exc}",
                    last_context_source=context_source,
                    last_analyst_mode=analyst_mode,
                    last_target_subdirectory=target_subdirectory,
                ),
                status_code=422,
            )
        encoded_subdirectory = quote(run_result.target_subdirectory, safe="")
        return RedirectResponse(
            url=f"/runs/{run_result.run_id}?created=1&target_subdirectory={encoded_subdirectory}",
            status_code=303,
        )

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    async def view_run(
        run_id: str,
        created: int | None = None,
        target_subdirectory: str | None = None,
    ) -> Response:
        if not root_status.is_usable or root_status.resolved_root is None:
            return HTMLResponse(
                content=_render_error_page(
                    title="Run Read Error",
                    message=(
                        "artifacts_root_unavailable: "
                        f"{_artifacts_root_unavailable_message(root_status=root_status)}"
                    ),
                    back_href="/",
                    back_label="Back to runs",
                ),
                status_code=422,
            )

        detail_root = root_status.resolved_root
        normalized_target_subdirectory: str | None = None
        if target_subdirectory is not None:
            try:
                detail_root, normalized_target_subdirectory = _resolve_target_subdirectory(
                    artifacts_root=root_status.resolved_root,
                    target_subdirectory=target_subdirectory,
                    create=False,
                )
            except ValueError as exc:
                if created == 1:
                    return HTMLResponse(
                        content=_render_error_page(
                            title="Trigger Result Unavailable",
                            message=_build_trigger_result_unavailable_message(
                                run_id=run_id,
                                target_subdirectory=target_subdirectory,
                                detail_error=str(exc),
                            ),
                            back_href="/",
                            back_label="Back to runs",
                        ),
                        status_code=422,
                    )
                return HTMLResponse(
                    content=_render_error_page(
                        title="Run Read Error",
                        message=str(exc),
                        back_href="/",
                        back_label="Back to runs",
                    ),
                    status_code=422,
                )

        try:
            detail = read_review_artifact_run_detail(
                artifacts_root=detail_root,
                run_id=run_id,
            )
        except ValueError as exc:
            if created == 1:
                return HTMLResponse(
                    content=_render_error_page(
                        title="Trigger Result Unavailable",
                        message=_build_trigger_result_unavailable_message(
                            run_id=run_id,
                            target_subdirectory=normalized_target_subdirectory,
                            detail_error=str(exc),
                        ),
                        back_href="/",
                        back_label="Back to runs",
                    ),
                    status_code=422,
                )
            status_code = 404 if str(exc).startswith("artifact_run_not_found") else 422
            return HTMLResponse(
                content=_render_error_page(
                    title="Run Read Error",
                    message=str(exc),
                    back_href="/",
                    back_label="Back to runs",
                ),
                status_code=status_code,
            )

        return HTMLResponse(
            content=_render_detail_page(
                detail=detail,
                created_via_trigger=(created == 1),
                target_subdirectory=normalized_target_subdirectory,
            )
        )

    return app


def discover_review_artifact_runs(*, artifacts_root: Path) -> list[ArtifactRunListItem]:
    """Enumerate deterministic valid run list records from bounded artifact files."""

    return discover_review_artifact_history(artifacts_root=artifacts_root).runs


def discover_review_artifact_history(*, artifacts_root: Path) -> ArtifactRunHistory:
    """Enumerate deterministic run history with explicit safe file-read issues."""

    root = _resolve_artifacts_root(artifacts_root)
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

        status_label = _status_label(status=status, failure_stage=failure_stage)
        updated_at_epoch_ns = json_path.stat().st_mtime_ns
        runs.append(
            ArtifactRunListItem(
                run_id=run_id,
                theme_id=theme_id,
                status=status,
                failure_stage=failure_stage,
                status_label=status_label,
                updated_at_epoch_ns=updated_at_epoch_ns,
                updated_at_label=_format_timestamp_ns(updated_at_epoch_ns),
                markdown_path=str(markdown_path),
                json_path=str(json_path),
            )
        )

    return ArtifactRunHistory(runs=runs, issues=issues)


def trigger_review_artifact_run(
    *,
    artifacts_root: Path,
    context_source: str,
    analyst_mode: str = "stub",
    target_subdirectory: str = _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY,
) -> TriggerRunResult:
    """Run one synchronous artifact-generation invocation and return the resulting run id."""

    root = _resolve_artifacts_root(artifacts_root)
    target_directory, normalized_target_subdirectory = _resolve_target_subdirectory(
        artifacts_root=root,
        target_subdirectory=target_subdirectory,
        create=True,
    )
    context_bundle = _load_context_bundle_from_source(context_source=context_source)
    analyst = _build_trigger_analyst(mode=analyst_mode)
    entry_result = run_analysis_and_write_review_artifacts(
        context_bundle=context_bundle,
        analyst=analyst,
        target_directory=target_directory,
    )
    run_json_path = Path(
        entry_result.entry_result.artifact_flow.flow_result.file_write_result.json_file_path
    )
    return TriggerRunResult(
        run_id=_normalize_run_id(run_json_path.stem),
        target_subdirectory=normalized_target_subdirectory,
    )


def read_review_artifact_run_detail(*, artifacts_root: Path, run_id: str) -> ArtifactRunDetail:
    """Read one run detail strictly from files under the configured artifacts root."""

    root = _resolve_artifacts_root(artifacts_root)
    normalized_run_id = _normalize_run_id(run_id)

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
        status_label=_status_label(status=status, failure_stage=failure_stage),
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


def _resolve_artifacts_root(artifacts_root: str | Path | None) -> Path:
    status = _resolve_artifacts_root_status(artifacts_root)
    if status.is_usable and status.resolved_root is not None:
        return status.resolved_root
    raise ValueError(_artifacts_root_unavailable_message(root_status=status))


def _resolve_artifacts_root_status(artifacts_root: str | Path | None) -> ArtifactsRootStatus:
    configured_value: str | None = None
    candidate: Path | None = None

    if artifacts_root is None:
        env_value = os.getenv(_ARTIFACTS_ROOT_ENV, "").strip()
        if not env_value:
            return ArtifactsRootStatus(
                state="not_configured",
                configured_value=None,
                resolved_root=None,
                message=(
                    "Artifacts root is not configured. Set "
                    f"{_ARTIFACTS_ROOT_ENV} or pass artifacts_root when creating the app."
                ),
            )
        configured_value = env_value
        candidate = Path(env_value)
    elif isinstance(artifacts_root, Path):
        configured_value = str(artifacts_root)
        candidate = artifacts_root
    elif isinstance(artifacts_root, str):
        stripped = artifacts_root.strip()
        if not stripped:
            return ArtifactsRootStatus(
                state="configured_invalid_or_unreadable",
                configured_value=artifacts_root,
                resolved_root=None,
                message="Configured artifacts root is invalid: path string is empty.",
            )
        configured_value = stripped
        candidate = Path(stripped)
    else:
        raise ValueError("artifacts_root must be a path-like string or Path.")

    assert candidate is not None
    try:
        resolved_candidate = candidate.resolve(strict=False)
    except OSError:
        return ArtifactsRootStatus(
            state="configured_invalid_or_unreadable",
            configured_value=configured_value,
            resolved_root=None,
            message="Configured artifacts root is unreadable or invalid.",
        )

    if not resolved_candidate.exists():
        return ArtifactsRootStatus(
            state="configured_missing",
            configured_value=configured_value,
            resolved_root=None,
            message="Configured artifacts root is missing on disk.",
        )
    if not resolved_candidate.is_dir():
        return ArtifactsRootStatus(
            state="configured_invalid_or_unreadable",
            configured_value=configured_value,
            resolved_root=None,
            message="Configured artifacts root is invalid: path is not a directory.",
        )

    required_access = os.R_OK | os.W_OK | os.X_OK
    if not os.access(resolved_candidate, required_access):
        return ArtifactsRootStatus(
            state="configured_invalid_or_unreadable",
            configured_value=configured_value,
            resolved_root=None,
            message=(
                "Configured artifacts root is unreadable or unwritable; read/write access "
                "is required."
            ),
        )

    return ArtifactsRootStatus(
        state="configured_readable",
        configured_value=str(resolved_candidate),
        resolved_root=resolved_candidate,
        message="Configured artifacts root is readable and writable.",
    )


def _discover_history_for_root_status(*, root_status: ArtifactsRootStatus) -> ArtifactRunHistory:
    if not root_status.is_usable or root_status.resolved_root is None:
        return ArtifactRunHistory(runs=[], issues=[])
    return discover_review_artifact_history(artifacts_root=root_status.resolved_root)


def _artifacts_root_unavailable_message(*, root_status: ArtifactsRootStatus) -> str:
    if root_status.state == "not_configured":
        return (
            "artifacts_root is required unless "
            f"{_ARTIFACTS_ROOT_ENV} is configured."
        )
    if root_status.state == "configured_missing":
        return "artifacts_root must reference an existing directory."
    return "artifacts_root must reference a readable and writable directory."


def _resolve_target_subdirectory(
    *,
    artifacts_root: Path,
    target_subdirectory: str,
    create: bool,
) -> tuple[Path, str]:
    normalized_raw = target_subdirectory.strip()
    normalized = normalized_raw or _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY
    subdirectory_path = Path(normalized)

    if subdirectory_path.is_absolute():
        raise ValueError("target_subdirectory must be a relative path under artifacts root.")

    safe_parts: list[str] = []
    for part in subdirectory_path.parts:
        if part in {"", ".", ".."}:
            raise ValueError(
                "target_subdirectory must not contain empty, '.' , or '..' path segments."
            )
        if not _TARGET_SUBDIRECTORY_SEGMENT_PATTERN.fullmatch(part):
            raise ValueError(
                "target_subdirectory segments may only include letters, numbers, '.', '_' , or '-'."
            )
        safe_parts.append(part)

    if not safe_parts:
        raise ValueError("target_subdirectory must contain at least one safe path segment.")

    normalized_subdirectory = "/".join(safe_parts)
    target_directory = (artifacts_root / normalized_subdirectory).resolve()
    try:
        target_directory.relative_to(artifacts_root)
    except ValueError as exc:
        raise ValueError("target_subdirectory must stay within artifacts root.") from exc

    if create:
        try:
            target_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValueError(
                "target_subdirectory could not be created under artifacts root."
            ) from exc

    return target_directory, normalized_subdirectory


def _build_trigger_result_unavailable_message(
    *,
    run_id: str,
    target_subdirectory: str | None,
    detail_error: str,
) -> str:
    target_context = target_subdirectory if target_subdirectory is not None else "(not provided)"
    return (
        "trigger_result_unavailable: newly triggered run is missing or partially readable. "
        f"run_id={run_id}; target_subdirectory={target_context}; detail_error={detail_error}"
    )


def _load_context_bundle_from_source(*, context_source: str) -> OpportunityContextBundle:
    normalized_source = context_source.strip()
    if not normalized_source:
        raise ValueError("context_source is required and must point to a JSON file.")

    source_path = Path(normalized_source)
    if source_path.suffix.lower() != ".json":
        raise ValueError("context_source must reference a .json file path.")
    if not source_path.exists():
        raise ValueError("context_source file does not exist.")
    if not source_path.is_file():
        raise ValueError("context_source must reference a file path.")

    try:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("context_source must contain valid JSON.") from exc

    try:
        return OpportunityContextBundle.model_validate(payload)
    except ValueError as exc:
        raise ValueError("context_source JSON must validate as OpportunityContextBundle.") from exc


def _build_trigger_analyst(*, mode: str) -> AnalystProtocol:
    if mode == "stub":
        return DeterministicStubAnalyst()
    if mode == "analyst_timeout":
        return _TimeoutAnalyst()
    if mode == "analyst_transport":
        return _TransportAnalyst()
    if mode == "reasoning_parse":
        return _MalformedAnalyst()
    raise ValueError(
        "analyst_mode must be one of "
        "stub/analyst_timeout/analyst_transport/reasoning_parse."
    )


def _normalize_run_id(run_id: str) -> str:
    normalized = run_id.strip()
    if not normalized:
        raise ValueError("artifact_run_id_invalid: run_id must be a non-empty string.")
    if not _RUN_ID_PATTERN.fullmatch(normalized):
        raise ValueError("artifact_run_id_invalid: run_id contains invalid characters.")
    return normalized


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


def _status_label(
    *,
    status: Literal["success", "failed"],
    failure_stage: AnalysisRunFailureStage | None,
) -> str:
    if status == "success":
        return "SUCCESS"
    if failure_stage is None:
        return "FAILED"
    return f"FAILED ({failure_stage})"


def _format_timestamp_ns(timestamp_ns: int) -> str:
    timestamp_seconds = timestamp_ns / 1_000_000_000
    formatted = datetime.fromtimestamp(timestamp_seconds, tz=UTC)
    return formatted.isoformat(timespec="seconds")


def _render_list_page(
    *,
    history: ArtifactRunHistory,
    root_status: ArtifactsRootStatus,
    trigger_error: str | None,
    last_context_source: str,
    last_analyst_mode: str,
    last_target_subdirectory: str,
) -> str:
    rows: list[str] = []
    for run in history.runs:
        status_badge = _render_status_badge(status=run.status, failure_stage=run.failure_stage)
        failure_stage = run.failure_stage if run.failure_stage is not None else "none"
        rows.append(
            "<tr>"
            f"<td><a href=\"/runs/{html.escape(run.run_id)}\">{html.escape(run.run_id)}</a></td>"
            f"<td>{html.escape(run.theme_id)}</td>"
            f"<td>{status_badge}</td>"
            f"<td>{html.escape(failure_stage)}</td>"
            f"<td>{html.escape(run.updated_at_label)}</td>"
            "</tr>"
        )

    table_rows = "".join(rows) if rows else "<tr><td colspan=\"5\">No runs found.</td></tr>"
    error_block = ""
    if trigger_error is not None:
        error_block = (
            "<p style=\"color:#b91c1c;font-weight:600;\">Trigger Error: "
            f"{html.escape(trigger_error)}</p>"
        )
    issue_rows: list[str] = []
    for issue in history.issues:
        issue_rows.append(
            "<tr>"
            f"<td>{html.escape(issue.run_id)}</td>"
            f"<td>{html.escape(issue.issue_kind)}</td>"
            f"<td>{html.escape(issue.issue_message)}</td>"
            f"<td>{html.escape(issue.json_path)}</td>"
            "</tr>"
        )
    issues_block = ""
    if issue_rows:
        issues_block = (
            "<h2>Run Issues</h2>"
            "<p>Some run files are incomplete or invalid and were safely skipped from details.</p>"
            "<table><thead><tr><th>Run</th><th>Issue</th><th>Message</th><th>JSON Path</th>"
            f"</tr></thead><tbody>{''.join(issue_rows)}</tbody></table>"
        )

    selected_mode = (
        last_analyst_mode if last_analyst_mode in _TRIGGER_ANALYST_MODE_CHOICES else "stub"
    )
    mode_options: list[str] = []
    for mode in _TRIGGER_ANALYST_MODE_CHOICES:
        selected_attr = " selected" if mode == selected_mode else ""
        mode_options.append(
            f"<option value=\"{html.escape(mode)}\"{selected_attr}>{html.escape(mode)}</option>"
        )
    mode_options_html = "".join(mode_options)
    root_status_label = _render_artifacts_root_state_label(root_status=root_status)
    root_status_class = (
        "root-ok" if root_status.is_usable else "root-problem"
    )
    configured_value = (
        html.escape(root_status.configured_value)
        if root_status.configured_value is not None
        else f"(unset; {_ARTIFACTS_ROOT_ENV} is empty)"
    )
    root_message_html = html.escape(root_status.message)
    root_block = (
        "<h2>Artifacts Root Status</h2>"
        f"<div class=\"root-status {root_status_class}\">"
        f"<p><strong>Status:</strong> {html.escape(root_status_label)}</p>"
        f"<p><strong>Configured Value:</strong> <code>{configured_value}</code></p>"
        f"<p>{root_message_html}</p>"
        "</div>"
    )
    disable_trigger_attr = " disabled" if not root_status.is_usable else ""
    trigger_disabled_block = ""
    if not root_status.is_usable:
        trigger_disabled_block = (
            "<p style=\"color:#991b1b;font-weight:600;\">"
            "Triggering is unavailable until artifacts root configuration is fixed."
            "</p>"
        )
    context_source_input = html.escape(last_context_source)
    target_subdirectory_input = html.escape(last_target_subdirectory.strip())

    return (
        "<!doctype html>"
        "<html><head><meta charset=\"utf-8\"><title>Review Artifacts</title>"
        "<style>"
        "body{font-family:ui-sans-serif,system-ui;padding:20px;background:#f8fafc;color:#111827;}"
        "table{border-collapse:collapse;width:100%;background:#fff;}"
        "th,td{border:1px solid #d1d5db;padding:8px;text-align:left;}"
        "th{background:#eef2ff;}"
        "a{color:#1d4ed8;text-decoration:none;}"
        ".badge{display:inline-block;padding:2px 8px;border-radius:999px;font-weight:600;}"
        ".badge-success{background:#dcfce7;color:#166534;}"
        ".badge-failed{background:#fee2e2;color:#991b1b;}"
        ".root-status{border:1px solid #d1d5db;padding:12px;background:#fff;margin-bottom:8px;}"
        ".root-ok{border-color:#86efac;background:#f0fdf4;}"
        ".root-problem{border-color:#fca5a5;background:#fef2f2;}"
        "input,select,button{font:inherit;padding:6px;border:1px solid #d1d5db;border-radius:4px;}"
        "label{font-weight:600;display:block;margin-bottom:4px;}"
        ".help{font-size:12px;color:#4b5563;margin-top:4px;}"
        ".form-grid{display:grid;grid-template-columns:2fr 1fr;gap:12px;max-width:920px;}"
        ".form-field{background:#fff;border:1px solid #d1d5db;padding:10px;}"
        ".form-actions{margin-top:10px;}"
        "</style></head><body>"
        "<h1>Review Artifacts</h1>"
        f"{root_block}"
        "<h2>Trigger Run</h2>"
        "<form action=\"/runs/trigger\" method=\"post\">"
        "<div class=\"form-grid\">"
        "<div class=\"form-field\">"
        "<label for=\"context_source\">Context Source JSON Path</label>"
        "<input id=\"context_source\" type=\"text\" name=\"context_source\" "
        "placeholder=\"/absolute/path/context_bundle.json\" "
        f"value=\"{context_source_input}\" required{disable_trigger_attr}>"
        "<p class=\"help\">Provide an existing OpportunityContextBundle JSON file path.</p>"
        "</div>"
        "<div class=\"form-field\">"
        "<label for=\"target_subdirectory\">Target Subdirectory</label>"
        "<input id=\"target_subdirectory\" type=\"text\" name=\"target_subdirectory\" "
        f"value=\"{target_subdirectory_input}\" required{disable_trigger_attr}>"
        "<p class=\"help\">Relative subdirectory under artifacts root; "
        "safe default isolates UI-triggered runs.</p>"
        "</div>"
        "<div class=\"form-field\">"
        "<label for=\"analyst_mode\">Analyst Mode</label>"
        f"<select id=\"analyst_mode\" name=\"analyst_mode\"{disable_trigger_attr}>"
        f"{mode_options_html}</select>"
        "<p class=\"help\">Use `stub` for normal deterministic success or choose "
        "a failure mode.</p>"
        "</div>"
        "</div>"
        "<div class=\"form-actions\">"
        f"<button type=\"submit\"{disable_trigger_attr}>Run Analysis</button>"
        "</div>"
        "</form>"
        f"{trigger_disabled_block}"
        f"{error_block}"
        "<h2>Runs</h2>"
        "<table><thead><tr>"
        "<th>Run</th><th>Theme ID</th><th>Status</th><th>Failure Stage</th><th>Updated</th>"
        f"</tr></thead><tbody>{table_rows}</tbody></table>"
        f"{issues_block}"
        "</body></html>"
    )


def _render_artifacts_root_state_label(*, root_status: ArtifactsRootStatus) -> str:
    if root_status.state == "configured_readable":
        return "configured and readable"
    if root_status.state == "configured_missing":
        return "configured but missing"
    if root_status.state == "configured_invalid_or_unreadable":
        return "configured but unreadable/invalid"
    return "not configured"


def _render_status_badge(
    *,
    status: Literal["success", "failed"],
    failure_stage: AnalysisRunFailureStage | None,
) -> str:
    label = _status_label(status=status, failure_stage=failure_stage)
    class_name = "badge-success" if status == "success" else "badge-failed"
    return f"<span class=\"badge {class_name}\">{html.escape(label)}</span>"


def _render_detail_page(
    *,
    detail: ArtifactRunDetail,
    created_via_trigger: bool,
    target_subdirectory: str | None,
) -> str:
    failure_stage = detail.run.failure_stage if detail.run.failure_stage is not None else "none"
    status_badge = _render_status_badge(
        status=detail.run.status,
        failure_stage=detail.run.failure_stage,
    )
    outcome_label = "SUCCESS" if detail.run.status == "success" else "FAILED"
    outcome_tone_class = (
        "outcome-success" if detail.run.status == "success" else "outcome-failed"
    )
    failure_stage_description = _failure_stage_description(
        status=detail.run.status,
        failure_stage=detail.run.failure_stage,
    )
    artifact_directory = str(Path(detail.run.json_path).parent)
    target_subdirectory_display = (
        target_subdirectory if target_subdirectory is not None else "(not provided)"
    )
    markdown_display, markdown_truncated, markdown_total_chars = _bounded_display_text(
        detail.markdown_content,
        max_chars=_DETAIL_MARKDOWN_MAX_CHARS,
    )
    json_pretty = json.dumps(detail.json_content, indent=2, sort_keys=True)
    json_display, json_truncated, json_total_chars = _bounded_display_text(
        json_pretty,
        max_chars=_DETAIL_JSON_MAX_CHARS,
    )
    markdown_block = html.escape(markdown_display)
    json_block = html.escape(json_display)
    markdown_notice = ""
    if markdown_truncated:
        markdown_notice = (
            "<p class=\"truncate\">Markdown content display truncated for safety: "
            f"showing first {_DETAIL_MARKDOWN_MAX_CHARS} of {markdown_total_chars} characters.</p>"
        )
    json_notice = ""
    if json_truncated:
        json_notice = (
            "<p class=\"truncate\">JSON content display truncated for safety: "
            f"showing first {_DETAIL_JSON_MAX_CHARS} of {json_total_chars} characters.</p>"
        )
    created_block = ""
    if created_via_trigger:
        created_block = (
            "<section class=\"section\" style=\"border-color:#86efac;background:#f0fdf4;\">"
            "<h2>Trigger Result Summary</h2>"
            "<p style=\"color:#065f46;font-weight:600;\">Run created via trigger and loaded.</p>"
            "<dl class=\"meta-grid\">"
            f"<dt>Run ID</dt><dd>{html.escape(detail.run.run_id)}</dd>"
            f"<dt>Theme ID</dt><dd>{html.escape(detail.run.theme_id)}</dd>"
            f"<dt>Run Outcome</dt><dd>{status_badge}</dd>"
            f"<dt>Failure Stage</dt><dd>{html.escape(failure_stage)}</dd>"
            f"<dt>Target Subdirectory</dt><dd>{html.escape(target_subdirectory_display)}</dd>"
            f"<dt>Artifact Directory</dt><dd>{html.escape(artifact_directory)}</dd>"
            "</dl>"
            "<p style=\"margin-top:8px;color:#065f46;\">Inspect outcome and artifact content "
            "sections below for full details.</p>"
            "</section>"
        )

    return (
        "<!doctype html>"
        "<html><head><meta charset=\"utf-8\"><title>Review Artifact Detail</title>"
        "<style>"
        "body{font-family:ui-sans-serif,system-ui;padding:20px;background:#f8fafc;color:#111827;}"
        ".badge{display:inline-block;padding:2px 8px;border-radius:999px;font-weight:600;}"
        ".badge-success{background:#dcfce7;color:#166534;}"
        ".badge-failed{background:#fee2e2;color:#991b1b;}"
        ".section{margin-top:18px;background:#fff;border:1px solid #d1d5db;padding:12px;}"
        ".meta-grid{display:grid;grid-template-columns:140px 1fr;gap:6px 10px;}"
        ".outcome{border-width:2px;}"
        ".outcome-success{border-color:#86efac;background:#f0fdf4;}"
        ".outcome-failed{border-color:#fca5a5;background:#fef2f2;}"
        ".outcome-label{font-size:24px;font-weight:700;margin:0 0 8px 0;}"
        "pre{white-space:pre-wrap;word-break:break-word;background:#fff;border:1px solid #d1d5db;"
        "padding:12px;max-height:540px;overflow:auto;}"
        "dt{font-weight:600;}"
        ".truncate{background:#fffbeb;color:#92400e;border:1px solid #fcd34d;padding:8px;}"
        "a{color:#1d4ed8;text-decoration:none;}"
        "</style></head><body>"
        "<p><a href=\"/\">Back to runs</a></p>"
        f"{created_block}"
        "<h1>Review Artifact Detail</h1>"
        f"<section class=\"section outcome {outcome_tone_class}\">"
        "<h2>Outcome Summary</h2>"
        f"<p class=\"outcome-label\">{html.escape(outcome_label)}</p>"
        "<dl class=\"meta-grid\">"
        f"<dt>Status Label</dt><dd>{html.escape(detail.run.status_label)}</dd>"
        f"<dt>Failure Stage</dt><dd>{html.escape(failure_stage)}</dd>"
        f"<dt>Failure Context</dt><dd>{html.escape(failure_stage_description)}</dd>"
        "</dl>"
        "</section>"
        "<section class=\"section\">"
        "<h2>Run Metadata</h2>"
        "<dl class=\"meta-grid\">"
        f"<dt>Run</dt><dd>{html.escape(detail.run.run_id)}</dd>"
        f"<dt>Theme ID</dt><dd>{html.escape(detail.run.theme_id)}</dd>"
        f"<dt>Status</dt><dd>{status_badge}</dd>"
        f"<dt>Failure Stage</dt><dd>{html.escape(failure_stage)}</dd>"
        f"<dt>Updated</dt><dd>{html.escape(detail.run.updated_at_label)}</dd>"
        "</dl>"
        "</section>"
        "<section class=\"section\">"
        "<h2>Artifact Paths</h2>"
        "<dl class=\"meta-grid\">"
        f"<dt>Target Subdirectory</dt><dd>{html.escape(target_subdirectory_display)}</dd>"
        f"<dt>Artifact Directory</dt><dd>{html.escape(artifact_directory)}</dd>"
        f"<dt>Markdown Path</dt><dd>{html.escape(detail.run.markdown_path)}</dd>"
        f"<dt>JSON Path</dt><dd>{html.escape(detail.run.json_path)}</dd>"
        f"<dt>Markdown Size</dt><dd>{len(detail.markdown_content)} chars</dd>"
        f"<dt>JSON Size</dt><dd>{len(json_pretty)} chars</dd>"
        "</dl>"
        "</section>"
        "<section class=\"section\">"
        "<h2>Artifact Content</h2>"
        "<h3>Markdown Content</h3>"
        f"{markdown_notice}"
        f"<pre>{markdown_block}</pre>"
        "<h3>JSON Content</h3>"
        f"{json_notice}"
        f"<pre>{json_block}</pre>"
        "</section>"
        "</body></html>"
    )


def _bounded_display_text(value: str, *, max_chars: int) -> tuple[str, bool, int]:
    total_chars = len(value)
    if total_chars <= max_chars:
        return value, False, total_chars
    return value[:max_chars], True, total_chars


def _failure_stage_description(
    *,
    status: Literal["success", "failed"],
    failure_stage: AnalysisRunFailureStage | None,
) -> str:
    if status == "success":
        return "No failure stage. Run completed successfully."
    if failure_stage is None:
        return "Failure stage is unavailable for this failed run."
    return _FAILURE_STAGE_DESCRIPTIONS[failure_stage]


def _render_error_page(*, title: str, message: str, back_href: str, back_label: str) -> str:
    return (
        "<!doctype html>"
        f"<html><head><meta charset=\"utf-8\"><title>{html.escape(title)}</title>"
        "<style>"
        "body{font-family:ui-sans-serif,system-ui;padding:20px;background:#f8fafc;color:#111827;}"
        "a{color:#1d4ed8;text-decoration:none;}"
        ".error{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;padding:12px;}"
        "</style></head><body>"
        f"<p><a href=\"{html.escape(back_href)}\">{html.escape(back_label)}</a></p>"
        f"<h1>{html.escape(title)}</h1>"
        f"<div class=\"error\">{html.escape(message)}</div>"
        "</body></html>"
    )


class _TimeoutAnalyst(AnalystProtocol):
    is_stub = False

    def analyze(
        self,
        *,
        reasoning_input: ReasoningInputPacket,
        rendered_prompt: RenderedPromptPacket,
    ) -> AnalystResponsePayload:
        del reasoning_input, rendered_prompt
        raise LiveAnalystTimeoutError("operator_ui_simulated_timeout")


class _TransportAnalyst(AnalystProtocol):
    is_stub = False

    def analyze(
        self,
        *,
        reasoning_input: ReasoningInputPacket,
        rendered_prompt: RenderedPromptPacket,
    ) -> AnalystResponsePayload:
        del reasoning_input, rendered_prompt
        raise LiveAnalystTransportError("operator_ui_simulated_transport_failure")


class _MalformedAnalyst(AnalystProtocol):
    is_stub = False

    def analyze(
        self,
        *,
        reasoning_input: ReasoningInputPacket,
        rendered_prompt: RenderedPromptPacket,
    ) -> AnalystResponsePayload:
        del reasoning_input, rendered_prompt
        return '{"invalid_json_payload":'
