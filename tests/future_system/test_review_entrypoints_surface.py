"""Deterministic surface tests for future_system.review_entrypoints top-level flow."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.live_analyst.adapter import LiveAnalystAdapter
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.review_entrypoints.entry import run_analysis_and_write_review_artifacts
from future_system.runtime.models import AnalysisRunFailureStage
from future_system.runtime.stub_analyst import DeterministicStubAnalyst
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_RUNTIME_FIXTURE_PATH = Path("tests/fixtures/future_system/runtime/runtime_inputs.json")


def test_run_analysis_and_write_review_artifacts_success_writes_expected_outputs(
    tmp_path: Path,
) -> None:
    result = run_analysis_and_write_review_artifacts(
        context_bundle=_bundle("strong_complete"),
        analyst=DeterministicStubAnalyst(),
        target_directory=tmp_path,
    )
    entry_result = result.entry_result

    assert result.status == "success"
    assert entry_result.entry_kind == "analysis_success_review_entry"
    assert entry_result.status == "success"
    assert entry_result.theme_id == "theme_ctx_strong"
    assert entry_result.target_directory == str(tmp_path.resolve())
    assert entry_result.failure_stage is None
    assert entry_result.runtime_result.status == "success"
    assert entry_result.artifact_flow.status == "success"
    assert entry_result.run_flags == [
        "analysis_dry_run",
        "stub_analyst_used",
        "reasoning_parsed",
        "policy_computed",
    ]

    markdown_path = Path(
        entry_result.artifact_flow.flow_result.file_write_result.markdown_file_path
    )
    json_path = Path(entry_result.artifact_flow.flow_result.file_write_result.json_file_path)

    assert markdown_path.name == "theme_ctx_strong.analysis_success_export.md"
    assert json_path.name == "theme_ctx_strong.analysis_success_export.json"
    assert (
        markdown_path.read_text(encoding="utf-8")
        == entry_result.artifact_flow.flow_result.export_package.payload.markdown_document
    )
    assert json.loads(json_path.read_text(encoding="utf-8")) == (
        entry_result.artifact_flow.flow_result.export_package.model_dump(mode="json")
    )


@pytest.mark.parametrize(
    ("failure_stage", "expected_run_flags"),
    [
        ("analyst_timeout", ["analysis_dry_run", "analyst_timeout"]),
        ("analyst_transport", ["analysis_dry_run", "analyst_transport_failed"]),
        ("reasoning_parse", ["analysis_dry_run", "reasoning_parse_failed"]),
    ],
)
def test_run_analysis_and_write_review_artifacts_failure_preserves_stage_identity(
    tmp_path: Path,
    failure_stage: AnalysisRunFailureStage,
    expected_run_flags: list[str],
) -> None:
    result = run_analysis_and_write_review_artifacts(
        context_bundle=_bundle("strong_complete"),
        analyst=_failure_analyst(failure_stage),
        target_directory=tmp_path,
    )
    entry_result = result.entry_result

    assert result.status == "failed"
    assert entry_result.entry_kind == "analysis_failure_review_entry"
    assert entry_result.status == "failed"
    assert entry_result.theme_id == "theme_ctx_strong"
    assert entry_result.target_directory == str(tmp_path.resolve())
    assert entry_result.failure_stage == failure_stage
    assert entry_result.runtime_result.status == "failed"
    assert entry_result.artifact_flow.status == "failed"
    assert entry_result.run_flags == expected_run_flags

    markdown_path = Path(
        entry_result.artifact_flow.flow_result.file_write_result.markdown_file_path
    )
    json_path = Path(entry_result.artifact_flow.flow_result.file_write_result.json_file_path)
    markdown_text = markdown_path.read_text(encoding="utf-8")
    json_document = json.loads(json_path.read_text(encoding="utf-8"))

    assert (
        markdown_path.name
        == f"theme_ctx_strong.analysis_failure_export.{failure_stage}.md"
    )
    assert json_path.name == f"theme_ctx_strong.analysis_failure_export.{failure_stage}.json"
    assert f"- Failure Stage: `{failure_stage}`" in markdown_text
    assert json_document["payload"]["failure_stage"] == failure_stage
    assert "policy_decision" not in json_document["payload"]["json_payload"]


def test_run_analysis_and_write_review_artifacts_is_deterministic_for_same_inputs(
    tmp_path: Path,
) -> None:
    context_bundle = _bundle("strong_complete")
    analyst = DeterministicStubAnalyst()

    first = run_analysis_and_write_review_artifacts(
        context_bundle=context_bundle,
        analyst=analyst,
        target_directory=tmp_path,
    )
    second = run_analysis_and_write_review_artifacts(
        context_bundle=context_bundle,
        analyst=analyst,
        target_directory=tmp_path,
    )

    assert first.model_dump(mode="json") == second.model_dump(mode="json")

    first_markdown = Path(
        first.entry_result.artifact_flow.flow_result.file_write_result.markdown_file_path
    )
    second_markdown = Path(
        second.entry_result.artifact_flow.flow_result.file_write_result.markdown_file_path
    )
    first_json = Path(first.entry_result.artifact_flow.flow_result.file_write_result.json_file_path)
    second_json = Path(
        second.entry_result.artifact_flow.flow_result.file_write_result.json_file_path
    )
    assert first_markdown.read_text(encoding="utf-8") == second_markdown.read_text(
        encoding="utf-8"
    )
    assert first_json.read_text(encoding="utf-8") == second_json.read_text(encoding="utf-8")


def _failure_analyst(failure_stage: AnalysisRunFailureStage) -> Any:
    if failure_stage == "analyst_timeout":
        return LiveAnalystAdapter(transport=_TimeoutTransport(), timeout_seconds=0.1)
    if failure_stage == "analyst_transport":
        return LiveAnalystAdapter(
            transport=_StaticTransport(response={"choices": []}),
            timeout_seconds=1.0,
        )
    malformed_case = _runtime_case("malformed_analyst_output")
    return _MalformedAnalyst(payload=malformed_case["malformed_payload"])


class _MalformedAnalyst:
    is_stub = False

    def __init__(self, *, payload: str) -> None:
        self._payload = payload

    def analyze(self, **_: object) -> str:
        return self._payload


class _StaticTransport:
    def __init__(self, *, response: Mapping[str, Any] | str) -> None:
        self._response = response

    def request(self, *, request: object) -> Mapping[str, Any] | str:
        del request
        return self._response


class _TimeoutTransport:
    def request(self, *, request: object) -> Mapping[str, Any] | str:
        del request
        raise TimeoutError("simulated timeout")


def _runtime_case(case_name: str) -> dict[str, Any]:
    payload = json.loads(_RUNTIME_FIXTURE_PATH.read_text(encoding="utf-8"))
    for item in payload:
        if item["case"] == case_name:
            return dict(item)
    raise AssertionError(f"Missing runtime fixture case: {case_name}")


def _bundle(case_name: str) -> Any:
    case = _context_cases()[case_name]
    return build_opportunity_context_bundle(
        theme_link_packet=case["theme_link"],
        polymarket_evidence_packet=case["polymarket_evidence"],
        divergence_packet=case["divergence"],
        crypto_evidence_packet=case["crypto_evidence"],
        comparison_packet=case["comparison"],
        news_evidence_packet=case["news_evidence"],
        candidate_packet=case["candidate"],
    )


def _context_cases() -> dict[str, dict[str, Any]]:
    payload = json.loads(_CONTEXT_FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        entry["case"]: {
            "theme_link": ThemeLinkPacket.model_validate(entry["theme_link"]),
            "polymarket_evidence": ThemeEvidencePacket.model_validate(entry["polymarket_evidence"]),
            "divergence": ThemeDivergencePacket.model_validate(entry["divergence"]),
            "crypto_evidence": ThemeCryptoEvidencePacket.model_validate(entry["crypto_evidence"]),
            "comparison": ThemeComparisonPacket.model_validate(entry["comparison"]),
            "news_evidence": ThemeNewsEvidencePacket.model_validate(entry["news_evidence"]),
            "candidate": CandidateSignalPacket.model_validate(entry["candidate"]),
        }
        for entry in payload
    }
