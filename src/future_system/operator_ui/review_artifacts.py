"""FastAPI operator UI for listing, triggering, and inspecting review artifact runs."""

from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path
from typing import Any, Literal, cast

from fastapi import FastAPI, Form, HTTPException, Response
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


class ArtifactRunListItem(BaseModel):
    """One bounded list-row record for a discovered artifact run."""

    run_id: str
    theme_id: str
    status: Literal["success", "failed"]
    failure_stage: AnalysisRunFailureStage | None = None
    markdown_path: str
    json_path: str

    @field_validator("run_id", "theme_id", "markdown_path", "json_path", mode="before")
    @classmethod
    def _normalize_text_fields(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("artifact list fields must be strings.")
        normalized = value.strip()
        if not normalized:
            raise ValueError("artifact list fields must be non-empty strings.")
        return normalized


class ArtifactRunDetail(BaseModel):
    """Bounded detail payload for one run used by the operator UI."""

    run: ArtifactRunListItem
    markdown_content: str
    json_content: dict[str, object]


def create_review_artifacts_operator_app(
    *,
    artifacts_root: str | Path | None = None,
) -> FastAPI:
    """Create a bounded read-only operator UI app scoped to one artifacts root."""

    resolved_root = _resolve_artifacts_root(artifacts_root)
    app = FastAPI(title="Future System Review Artifact Operator UI", version="0.1.0")
    app.state.artifacts_root = resolved_root

    @app.get("/", response_class=HTMLResponse)
    async def list_runs() -> str:
        runs = discover_review_artifact_runs(artifacts_root=resolved_root)
        return _render_list_page(
            runs=runs,
            artifacts_root=resolved_root,
            trigger_error=None,
            last_context_source="",
            last_analyst_mode="stub",
        )

    @app.post("/runs/trigger")
    async def trigger_run(
        context_source: str = Form(...),
        analyst_mode: str = Form("stub"),
    ) -> Response:
        try:
            run_id = trigger_review_artifact_run(
                artifacts_root=resolved_root,
                context_source=context_source,
                analyst_mode=analyst_mode,
            )
        except ValueError as exc:
            runs = discover_review_artifact_runs(artifacts_root=resolved_root)
            return HTMLResponse(
                content=_render_list_page(
                    runs=runs,
                    artifacts_root=resolved_root,
                    trigger_error=str(exc),
                    last_context_source=context_source,
                    last_analyst_mode=analyst_mode,
                ),
                status_code=422,
            )
        return RedirectResponse(url=f"/runs/{run_id}", status_code=303)

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    async def view_run(run_id: str) -> str:
        try:
            detail = read_review_artifact_run_detail(
                artifacts_root=resolved_root,
                run_id=run_id,
            )
        except ValueError as exc:
            message = str(exc)
            if message.startswith("artifact_run_not_found"):
                raise HTTPException(status_code=404, detail=message) from exc
            raise HTTPException(status_code=422, detail=message) from exc

        return _render_detail_page(detail=detail)

    return app


def discover_review_artifact_runs(*, artifacts_root: Path) -> list[ArtifactRunListItem]:
    """Enumerate deterministic run list records from bounded artifact files."""

    root = _resolve_artifacts_root(artifacts_root)
    runs: list[ArtifactRunListItem] = []

    for json_path in sorted(root.glob("*.json"), key=lambda path: path.name):
        run_id = json_path.stem
        if not _RUN_ID_PATTERN.fullmatch(run_id):
            continue
        markdown_path = root / f"{run_id}.md"
        payload = _read_export_json(json_path=json_path)
        runs.append(
            ArtifactRunListItem(
                run_id=run_id,
                theme_id=_require_string(payload.get("theme_id"), "theme_id"),
                status=_require_status(payload.get("status")),
                failure_stage=_optional_failure_stage(payload),
                markdown_path=str(markdown_path),
                json_path=str(json_path),
            )
        )

    return runs


def trigger_review_artifact_run(
    *,
    artifacts_root: Path,
    context_source: str,
    analyst_mode: str = "stub",
) -> str:
    """Run one synchronous artifact-generation invocation and return the resulting run id."""

    root = _resolve_artifacts_root(artifacts_root)
    context_bundle = _load_context_bundle_from_source(context_source=context_source)
    analyst = _build_trigger_analyst(mode=analyst_mode)
    entry_result = run_analysis_and_write_review_artifacts(
        context_bundle=context_bundle,
        analyst=analyst,
        target_directory=root,
    )
    run_json_path = Path(
        entry_result.entry_result.artifact_flow.flow_result.file_write_result.json_file_path
    )
    return _normalize_run_id(run_json_path.stem)


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
    run = ArtifactRunListItem(
        run_id=normalized_run_id,
        theme_id=_require_string(payload.get("theme_id"), "theme_id"),
        status=_require_status(payload.get("status")),
        failure_stage=_optional_failure_stage(payload),
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
    candidate: Path
    if artifacts_root is None:
        env_value = os.getenv(_ARTIFACTS_ROOT_ENV, "").strip()
        if not env_value:
            raise ValueError(
                f"artifacts_root is required unless {_ARTIFACTS_ROOT_ENV} is configured."
            )
        candidate = Path(env_value)
    elif isinstance(artifacts_root, Path):
        candidate = artifacts_root
    elif isinstance(artifacts_root, str):
        stripped = artifacts_root.strip()
        if not stripped:
            raise ValueError("artifacts_root must be a non-empty path string.")
        candidate = Path(stripped)
    else:
        raise ValueError("artifacts_root must be a path-like string or Path.")

    if not candidate.exists():
        raise ValueError("artifacts_root must reference an existing directory.")
    if not candidate.is_dir():
        raise ValueError("artifacts_root must reference a directory.")
    return candidate.resolve()


def _load_context_bundle_from_source(*, context_source: str) -> OpportunityContextBundle:
    normalized_source = context_source.strip()
    if not normalized_source:
        raise ValueError("context_source must be a non-empty path string.")

    source_path = Path(normalized_source)
    if not source_path.exists():
        raise ValueError("context_source must reference an existing file.")
    if not source_path.is_file():
        raise ValueError("context_source must reference a file.")

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


def _render_list_page(
    *,
    runs: list[ArtifactRunListItem],
    artifacts_root: Path,
    trigger_error: str | None,
    last_context_source: str,
    last_analyst_mode: str,
) -> str:
    rows: list[str] = []
    for run in runs:
        failure_stage = run.failure_stage if run.failure_stage is not None else "none"
        rows.append(
            "<tr>"
            f"<td><a href=\"/runs/{html.escape(run.run_id)}\">{html.escape(run.run_id)}</a></td>"
            f"<td>{html.escape(run.theme_id)}</td>"
            f"<td>{html.escape(run.status)}</td>"
            f"<td>{html.escape(failure_stage)}</td>"
            "</tr>"
        )

    table_rows = "".join(rows) if rows else "<tr><td colspan=\"4\">No runs found.</td></tr>"
    error_block = ""
    if trigger_error is not None:
        error_block = (
            "<p style=\"color:#b91c1c;font-weight:600;\">Trigger Error: "
            f"{html.escape(trigger_error)}</p>"
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

    return (
        "<!doctype html>"
        "<html><head><meta charset=\"utf-8\"><title>Review Artifacts</title>"
        "<style>"
        "body{font-family:ui-sans-serif,system-ui;padding:20px;background:#f8fafc;color:#111827;}"
        "table{border-collapse:collapse;width:100%;background:#fff;}"
        "th,td{border:1px solid #d1d5db;padding:8px;text-align:left;}"
        "th{background:#eef2ff;}"
        "a{color:#1d4ed8;text-decoration:none;}"
        "input,select,button{font:inherit;padding:6px;border:1px solid #d1d5db;border-radius:4px;}"
        "form{display:grid;grid-template-columns:1fr auto auto;gap:8px;max-width:900px;}"
        "</style></head><body>"
        "<h1>Review Artifacts</h1>"
        f"<p>Artifacts root: <code>{html.escape(str(artifacts_root))}</code></p>"
        "<h2>Trigger Run</h2>"
        "<form action=\"/runs/trigger\" method=\"post\">"
        "<input type=\"text\" name=\"context_source\" placeholder=\"/path/to/context_bundle.json\" "
        f"value=\"{html.escape(last_context_source)}\" required>"
        "<select name=\"analyst_mode\">"
        f"{mode_options_html}"
        "</select>"
        "<button type=\"submit\">Run</button>"
        "</form>"
        f"{error_block}"
        "<h2>Runs</h2>"
        "<table><thead><tr><th>Run</th><th>Theme ID</th><th>Status</th><th>Failure Stage</th>"
        f"</tr></thead><tbody>{table_rows}</tbody></table>"
        "</body></html>"
    )


def _render_detail_page(*, detail: ArtifactRunDetail) -> str:
    failure_stage = detail.run.failure_stage if detail.run.failure_stage is not None else "none"
    markdown_block = html.escape(detail.markdown_content)
    json_block = html.escape(json.dumps(detail.json_content, indent=2, sort_keys=True))

    return (
        "<!doctype html>"
        "<html><head><meta charset=\"utf-8\"><title>Review Artifact Detail</title>"
        "<style>"
        "body{font-family:ui-sans-serif,system-ui;padding:20px;background:#f8fafc;color:#111827;}"
        "pre{white-space:pre-wrap;word-break:break-word;background:#fff;border:1px solid #d1d5db;"
        "padding:12px;}"
        "dl{display:grid;grid-template-columns:140px 1fr;gap:6px 10px;}"
        "dt{font-weight:600;}"
        "a{color:#1d4ed8;text-decoration:none;}"
        "</style></head><body>"
        "<p><a href=\"/\">Back to runs</a></p>"
        "<h1>Review Artifact Detail</h1>"
        "<dl>"
        f"<dt>Run</dt><dd>{html.escape(detail.run.run_id)}</dd>"
        f"<dt>Theme ID</dt><dd>{html.escape(detail.run.theme_id)}</dd>"
        f"<dt>Status</dt><dd>{html.escape(detail.run.status)}</dd>"
        f"<dt>Failure Stage</dt><dd>{html.escape(failure_stage)}</dd>"
        f"<dt>Markdown Path</dt><dd>{html.escape(detail.run.markdown_path)}</dd>"
        f"<dt>JSON Path</dt><dd>{html.escape(detail.run.json_path)}</dd>"
        "</dl>"
        "<h2>Markdown</h2>"
        f"<pre>{markdown_block}</pre>"
        "<h2>JSON</h2>"
        f"<pre>{json_block}</pre>"
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
