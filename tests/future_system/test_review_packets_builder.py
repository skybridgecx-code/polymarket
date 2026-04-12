"""Builder behavior tests for deterministic runtime-result review packet conversion."""

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
from future_system.runtime.runner import run_analysis_pipeline_result
from future_system.runtime.stub_analyst import DeterministicStubAnalyst
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_RUNTIME_FIXTURE_PATH = Path("tests/fixtures/future_system/runtime/runtime_inputs.json")


def test_builder_converts_success_runtime_result_to_success_review_packet() -> None:
    result = run_analysis_pipeline_result(
        context_bundle=_bundle("strong_complete"),
        analyst=DeterministicStubAnalyst(),
    )

    review = build_analysis_review_packet(runtime_result=result)
    packet = review.review_packet

    assert review.status == "success"
    assert packet.packet_kind == "analysis_success"
    assert packet.status == "success"
    assert packet.theme_id == "theme_ctx_strong"
    assert packet.policy_decision == "allow"
    assert packet.reasoning_posture == "candidate"
    assert packet.candidate_posture == "candidate"
    assert (
        packet.summary_text
        == "theme_id=theme_ctx_strong; packet_kind=analysis_success; status=success; "
        "candidate_posture=candidate; reasoning_posture=candidate; "
        "policy_decision=allow; "
        "run_flags=analysis_dry_run,stub_analyst_used,reasoning_parsed,policy_computed."
    )


@pytest.mark.parametrize(
    ("failure_stage", "expected_run_flags", "expected_summary"),
    [
        (
            "analyst_timeout",
            ["analysis_dry_run", "analyst_timeout"],
            "theme_id=theme_ctx_strong; packet_kind=analysis_failure; status=failed; "
            "failure_stage=analyst_timeout; run_flags=analysis_dry_run,analyst_timeout.",
        ),
        (
            "analyst_transport",
            ["analysis_dry_run", "analyst_transport_failed"],
            "theme_id=theme_ctx_strong; packet_kind=analysis_failure; status=failed; "
            "failure_stage=analyst_transport; "
            "run_flags=analysis_dry_run,analyst_transport_failed.",
        ),
        (
            "reasoning_parse",
            ["analysis_dry_run", "reasoning_parse_failed"],
            "theme_id=theme_ctx_strong; packet_kind=analysis_failure; status=failed; "
            "failure_stage=reasoning_parse; "
            "run_flags=analysis_dry_run,reasoning_parse_failed.",
        ),
    ],
)
def test_builder_converts_each_runtime_failure_stage_to_failure_review_packet(
    failure_stage: str,
    expected_run_flags: list[str],
    expected_summary: str,
) -> None:
    review = build_analysis_review_packet(runtime_result=_failure_result(failure_stage))
    packet = review.review_packet

    assert review.status == "failed"
    assert packet.packet_kind == "analysis_failure"
    assert packet.status == "failed"
    assert packet.failure_stage == failure_stage
    assert packet.theme_id == "theme_ctx_strong"
    assert packet.run_flags == expected_run_flags
    assert packet.summary_text == expected_summary
    assert "policy_decision" not in packet.model_dump(mode="json")
    assert "reasoning_output" not in packet.model_dump(mode="json")


def test_builder_output_is_deterministic_for_same_runtime_result() -> None:
    result = run_analysis_pipeline_result(
        context_bundle=_bundle("strong_complete"),
        analyst=DeterministicStubAnalyst(),
    )

    first = build_analysis_review_packet(runtime_result=result)
    second = build_analysis_review_packet(runtime_result=result)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def _failure_result(failure_stage: str) -> Any:
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

    return run_analysis_pipeline_result(
        context_bundle=context_bundle,
        analyst=analyst,
    )


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
