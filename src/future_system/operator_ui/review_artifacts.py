"""FastAPI operator UI for listing, triggering, and inspecting review artifact runs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, Form, Response
from fastapi.responses import HTMLResponse

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.live_analyst.errors import LiveAnalystTimeoutError, LiveAnalystTransportError
from future_system.operator_ui.app_wiring import (
    DEFAULT_TRIGGER_TARGET_SUBDIRECTORY as _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY,
)
from future_system.operator_ui.app_wiring import (
    build_review_artifacts_operator_ui_assembly,
)
from future_system.operator_ui.artifact_reads import (
    ArtifactRunDetail,
    ArtifactRunHistory,
    ArtifactRunListItem,
    normalize_run_id,
)
from future_system.operator_ui.artifact_reads import (
    discover_review_artifact_history as _discover_review_artifact_history,
)
from future_system.operator_ui.artifact_reads import (
    discover_review_artifact_runs as _discover_review_artifact_runs,
)
from future_system.operator_ui.artifact_reads import (
    read_review_artifact_run_detail as _read_review_artifact_run_detail,
)
from future_system.operator_ui.root_status import resolve_artifacts_root
from future_system.operator_ui.route_handlers import (
    handle_list_runs_request as _handle_list_runs_request,
)
from future_system.operator_ui.route_handlers import (
    handle_trigger_run_request as _handle_trigger_run_request,
)
from future_system.operator_ui.route_handlers import (
    handle_view_run_request as _handle_view_run_request,
)
from future_system.reasoning_contracts.models import ReasoningInputPacket, RenderedPromptPacket
from future_system.review_entrypoints.entry import run_analysis_and_write_review_artifacts
from future_system.runtime.protocol import AnalystProtocol, AnalystResponsePayload
from future_system.runtime.stub_analyst import DeterministicStubAnalyst

_TARGET_SUBDIRECTORY_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


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

    assembly = build_review_artifacts_operator_ui_assembly(
        artifacts_root=artifacts_root,
        discover_review_artifact_history_fn=discover_review_artifact_history,
        trigger_review_artifact_run_fn=trigger_review_artifact_run,
        read_review_artifact_run_detail_fn=read_review_artifact_run_detail,
        resolve_target_subdirectory_fn=_resolve_target_subdirectory,
    )
    root_status = assembly.root_status
    config = assembly.config
    dependencies = assembly.dependencies
    app = FastAPI(title="Future System Review Artifact Operator UI", version="0.1.0")
    app.state.artifacts_root_status = root_status

    @app.get("/", response_class=HTMLResponse)
    async def list_runs() -> str:
        return _handle_list_runs_request(
            root_status=root_status,
            discover_review_artifact_history_fn=dependencies.discover_review_artifact_history_fn,
            trigger_error=None,
            last_context_source=config.default_trigger_context_source,
            last_analyst_mode=config.default_trigger_analyst_mode,
            last_target_subdirectory=config.default_target_subdirectory,
            trigger_analyst_mode_choices=config.trigger_analyst_mode_choices,
        )

    @app.post("/runs/trigger")
    async def trigger_run(
        context_source: str = Form(...),
        analyst_mode: str = Form(config.default_trigger_analyst_mode),
        target_subdirectory: str = Form(config.default_target_subdirectory),
    ) -> Response:
        return _handle_trigger_run_request(
            root_status=root_status,
            context_source=context_source,
            analyst_mode=analyst_mode,
            target_subdirectory=target_subdirectory,
            trigger_analyst_mode_choices=config.trigger_analyst_mode_choices,
            trigger_review_artifact_run_fn=dependencies.trigger_review_artifact_run_fn,
            discover_review_artifact_history_fn=dependencies.discover_review_artifact_history_fn,
        )

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    async def view_run(
        run_id: str,
        created: int | None = None,
        target_subdirectory: str | None = None,
    ) -> Response:
        return _handle_view_run_request(
            root_status=root_status,
            run_id=run_id,
            created=created,
            target_subdirectory=target_subdirectory,
            read_review_artifact_run_detail_fn=dependencies.read_review_artifact_run_detail_fn,
            resolve_target_subdirectory_fn=dependencies.resolve_target_subdirectory_fn,
        )

    return app


def discover_review_artifact_runs(*, artifacts_root: Path) -> list[ArtifactRunListItem]:
    """Enumerate deterministic valid run list records from bounded artifact files."""

    return _discover_review_artifact_runs(artifacts_root=artifacts_root)


def discover_review_artifact_history(*, artifacts_root: Path) -> ArtifactRunHistory:
    """Enumerate deterministic run history with explicit safe file-read issues."""

    return _discover_review_artifact_history(artifacts_root=artifacts_root)


def trigger_review_artifact_run(
    *,
    artifacts_root: Path,
    context_source: str,
    analyst_mode: str = "stub",
    target_subdirectory: str = _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY,
) -> TriggerRunResult:
    """Run one synchronous artifact-generation invocation and return the resulting run id."""

    root = resolve_artifacts_root(artifacts_root)
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
        run_id=normalize_run_id(run_json_path.stem),
        target_subdirectory=normalized_target_subdirectory,
    )


def read_review_artifact_run_detail(*, artifacts_root: Path, run_id: str) -> ArtifactRunDetail:
    """Read one run detail strictly from files under the configured artifacts root."""

    return _read_review_artifact_run_detail(
        artifacts_root=artifacts_root,
        run_id=run_id,
    )


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
