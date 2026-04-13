"""CLI entrypoint for running runtime analysis and writing review artifacts locally."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.live_analyst.errors import LiveAnalystTimeoutError, LiveAnalystTransportError
from future_system.reasoning_contracts.models import ReasoningInputPacket, RenderedPromptPacket
from future_system.review_entrypoints.entry import run_analysis_and_write_review_artifacts
from future_system.review_entrypoints.models import AnalysisReviewEntryEnvelope
from future_system.runtime.protocol import AnalystProtocol, AnalystResponsePayload
from future_system.runtime.stub_analyst import DeterministicStubAnalyst

_ANALYST_MODE_CHOICES = (
    "stub",
    "analyst_timeout",
    "analyst_transport",
    "reasoning_parse",
)


def main(argv: list[str] | None = None) -> int:
    """Run bounded review artifact CLI and print deterministic operator-safe summary output."""

    args = _build_parser().parse_args(argv)
    try:
        context_bundle = _load_context_bundle(context_source=args.context_source)
        analyst = _build_analyst(mode=args.analyst_mode)
        entry_result = run_analysis_and_write_review_artifacts(
            context_bundle=context_bundle,
            analyst=analyst,
            target_directory=args.target_directory,
        )
    except ValueError as exc:
        print(f"review_artifacts_cli_error: {exc}", file=sys.stderr)
        return 2

    print(_render_cli_summary(entry_result))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m future_system.cli.review_artifacts",
        description="Run deterministic runtime-to-review artifact flow for one context bundle.",
    )
    parser.add_argument(
        "--context-source",
        required=True,
        help="Path to JSON file containing an OpportunityContextBundle payload.",
    )
    parser.add_argument(
        "--target-directory",
        required=True,
        help="Directory where markdown/json review artifacts will be written.",
    )
    parser.add_argument(
        "--analyst-mode",
        default="stub",
        choices=_ANALYST_MODE_CHOICES,
        help=(
            "Analyst mode for deterministic execution: "
            "stub|analyst_timeout|analyst_transport|reasoning_parse."
        ),
    )
    return parser


def _load_context_bundle(*, context_source: str) -> OpportunityContextBundle:
    source_path = Path(context_source.strip())
    if not context_source.strip():
        raise ValueError("context_source must be a non-empty path string.")
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
    except ValidationError as exc:
        raise ValueError("context_source JSON must validate as OpportunityContextBundle.") from exc


def _build_analyst(*, mode: str) -> AnalystProtocol:
    if mode == "stub":
        return DeterministicStubAnalyst()
    if mode == "analyst_timeout":
        return _TimeoutAnalyst()
    if mode == "analyst_transport":
        return _TransportAnalyst()
    if mode == "reasoning_parse":
        return _MalformedAnalyst()
    raise ValueError(f"Unsupported analyst_mode: {mode}")


def _render_cli_summary(entry: AnalysisReviewEntryEnvelope) -> str:
    entry_result = entry.entry_result
    flow_result = entry_result.artifact_flow.flow_result
    file_write = flow_result.file_write_result

    summary: dict[str, object] = {
        "entry_kind": entry_result.entry_kind,
        "status": entry.status,
        "theme_id": entry_result.theme_id,
        "target_directory": entry_result.target_directory,
        "failure_stage": entry_result.failure_stage,
        "run_flags": list(entry_result.run_flags),
        "markdown_file_path": file_write.markdown_file_path,
        "json_file_path": file_write.json_file_path,
        "entry_summary": entry_result.entry_summary,
    }
    return json.dumps(summary, sort_keys=True, separators=(",", ":"))


class _TimeoutAnalyst(AnalystProtocol):
    is_stub = False

    def analyze(
        self,
        *,
        reasoning_input: ReasoningInputPacket,
        rendered_prompt: RenderedPromptPacket,
    ) -> AnalystResponsePayload:
        del reasoning_input, rendered_prompt
        raise LiveAnalystTimeoutError("cli_simulated_timeout")


class _TransportAnalyst(AnalystProtocol):
    is_stub = False

    def analyze(
        self,
        *,
        reasoning_input: ReasoningInputPacket,
        rendered_prompt: RenderedPromptPacket,
    ) -> AnalystResponsePayload:
        del reasoning_input, rendered_prompt
        raise LiveAnalystTransportError("cli_simulated_transport_failure")


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


if __name__ == "__main__":
    raise SystemExit(main())
