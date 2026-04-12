"""Deterministic rendering tests for future_system.review_renderers output surface."""

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
from future_system.review_packets.builder import build_analysis_review_packet
from future_system.review_renderers.renderer import (
    render_review_packet,
    render_review_packet_markdown,
    render_review_packet_text,
)
from future_system.runtime.runner import run_analysis_pipeline_result
from future_system.runtime.stub_analyst import DeterministicStubAnalyst
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_RUNTIME_FIXTURE_PATH = Path("tests/fixtures/future_system/runtime/runtime_inputs.json")


def test_success_rendering_is_deterministic_for_text_and_markdown() -> None:
    review_packet = _success_review_packet()

    text_a = render_review_packet_text(review_packet=review_packet)
    text_b = render_review_packet(review_packet=review_packet, output_format="text")
    markdown_a = render_review_packet_markdown(review_packet=review_packet)
    markdown_b = render_review_packet(review_packet=review_packet, output_format="markdown")

    assert text_a == text_b
    assert markdown_a == markdown_b
    assert "packet_kind=analysis_success" in text_a
    assert "failure_stage=" not in text_a
    assert "- Packet Kind: `analysis_success`" in markdown_a


@pytest.mark.parametrize(
    "failure_stage",
    ["analyst_timeout", "analyst_transport", "reasoning_parse"],
)
def test_failure_rendering_preserves_explicit_stage_identity(failure_stage: str) -> None:
    review_packet = _failure_review_packet(failure_stage)

    text = render_review_packet_text(review_packet=review_packet)
    markdown = render_review_packet_markdown(review_packet=review_packet)

    assert "packet_kind=analysis_failure" in text
    assert f"failure_stage={failure_stage}" in text
    assert "policy_decision=" not in text
    assert f"- Failure Stage: `{failure_stage}`" in markdown
    assert "- Packet Kind: `analysis_failure`" in markdown


def test_text_render_matches_expected_success_output_for_known_fixture() -> None:
    review_packet = _success_review_packet()
    packet = review_packet.review_packet

    rendered = render_review_packet_text(review_packet=review_packet)

    assert rendered == (
        "analysis_review_packet\n"
        "packet_kind=analysis_success\n"
        "status=success\n"
        f"theme_id={packet.theme_id}\n"
        f"candidate_posture={packet.candidate_posture}\n"
        f"reasoning_posture={packet.reasoning_posture}\n"
        f"policy_decision={packet.policy_decision}\n"
        f"decision_score={packet.decision_score:.3f}\n"
        f"readiness_score={packet.readiness_score:.3f}\n"
        f"risk_penalty={packet.risk_penalty:.3f}\n"
        f"run_flags={','.join(packet.run_flags)}\n"
        f"summary_text={packet.summary_text}\n"
        f"runtime_summary={packet.runtime_summary}"
    )


def test_render_review_packet_rejects_invalid_output_format() -> None:
    review_packet = _success_review_packet()

    with pytest.raises(ValueError, match="output_format must be either 'text' or 'markdown'"):
        render_review_packet(review_packet=review_packet, output_format="html")  # type: ignore[arg-type]


def _success_review_packet() -> Any:
    runtime_result = run_analysis_pipeline_result(
        context_bundle=_bundle("strong_complete"),
        analyst=DeterministicStubAnalyst(),
    )
    return build_analysis_review_packet(runtime_result=runtime_result)


def _failure_review_packet(failure_stage: str) -> Any:
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
    return build_analysis_review_packet(runtime_result=runtime_result)


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
