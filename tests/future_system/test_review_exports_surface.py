"""Deterministic surface tests for future_system.review_exports payload construction."""

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
from future_system.review_bundles.builder import build_review_bundle
from future_system.review_exports.builder import build_review_export_payloads
from future_system.runtime.runner import run_analysis_pipeline_result
from future_system.runtime.stub_analyst import DeterministicStubAnalyst
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_RUNTIME_FIXTURE_PATH = Path("tests/fixtures/future_system/runtime/runtime_inputs.json")


def test_build_review_export_payloads_success_contains_json_and_markdown_payloads() -> None:
    export_package = build_review_export_payloads(review_bundle=_success_bundle())

    assert export_package.status == "success"
    assert export_package.export_kind == "analysis_success_export"
    assert export_package.theme_id == "theme_ctx_strong"
    assert export_package.run_flags == [
        "analysis_dry_run",
        "stub_analyst_used",
        "reasoning_parsed",
        "policy_computed",
    ]
    assert export_package.payload.bundle_kind == "analysis_success_bundle"
    assert export_package.payload.packet_kind == "analysis_success"
    assert export_package.payload.json_payload["theme_id"] == "theme_ctx_strong"
    assert export_package.payload.json_payload["status"] == "success"
    assert "policy_decision" in export_package.payload.json_payload
    assert "# Analysis Review Export" in export_package.payload.markdown_document
    assert "- Export Kind: `analysis_success_export`" in export_package.payload.markdown_document
    assert (
        export_package.payload.export_summary
        == "theme_id=theme_ctx_strong; export_kind=analysis_success_export; status=success; "
        "run_flags=analysis_dry_run,stub_analyst_used,reasoning_parsed,policy_computed."
    )


@pytest.mark.parametrize(
    ("failure_stage", "expected_run_flags"),
    [
        ("analyst_timeout", ["analysis_dry_run", "analyst_timeout"]),
        ("analyst_transport", ["analysis_dry_run", "analyst_transport_failed"]),
        ("reasoning_parse", ["analysis_dry_run", "reasoning_parse_failed"]),
    ],
)
def test_build_review_export_payloads_failure_preserves_explicit_stage_identity(
    failure_stage: str,
    expected_run_flags: list[str],
) -> None:
    export_package = build_review_export_payloads(review_bundle=_failure_bundle(failure_stage))

    assert export_package.status == "failed"
    assert export_package.export_kind == "analysis_failure_export"
    assert export_package.theme_id == "theme_ctx_strong"
    assert export_package.run_flags == expected_run_flags
    assert export_package.payload.bundle_kind == "analysis_failure_bundle"
    assert export_package.payload.packet_kind == "analysis_failure"
    assert export_package.payload.failure_stage == failure_stage
    assert export_package.payload.json_payload["failure_stage"] == failure_stage
    assert "policy_decision" not in export_package.payload.json_payload
    assert "# Analysis Review Export" in export_package.payload.markdown_document
    assert (
        f"- Failure Stage: `{failure_stage}`" in export_package.payload.markdown_document
    )


def test_build_review_export_payloads_is_deterministic_for_same_input_bundle() -> None:
    bundle = _success_bundle()

    export_a = build_review_export_payloads(review_bundle=bundle)
    export_b = build_review_export_payloads(review_bundle=bundle)

    assert export_a.model_dump(mode="json") == export_b.model_dump(mode="json")


def _success_bundle() -> Any:
    runtime_result = run_analysis_pipeline_result(
        context_bundle=_bundle("strong_complete"),
        analyst=DeterministicStubAnalyst(),
    )
    return build_review_bundle(runtime_result=runtime_result)


def _failure_bundle(failure_stage: str) -> Any:
    context_bundle = _bundle("strong_complete")
    if failure_stage == "analyst_timeout":
        analyst: Any = LiveAnalystAdapter(
            transport=_TimeoutTransport(),
            timeout_seconds=0.1,
        )
    elif failure_stage == "analyst_transport":
        analyst = LiveAnalystAdapter(
            transport=_StaticTransport(response={"choices": []}),
            timeout_seconds=1.0,
        )
    else:
        malformed_case = _runtime_case("malformed_analyst_output")
        analyst = _MalformedAnalyst(payload=malformed_case["malformed_payload"])

    runtime_result = run_analysis_pipeline_result(
        context_bundle=context_bundle,
        analyst=analyst,
    )
    return build_review_bundle(runtime_result=runtime_result)


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
