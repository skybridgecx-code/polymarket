"""End-to-end dry-run pipeline tests for future_system.runtime.runner."""

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
from future_system.reasoning_contracts.builder import build_reasoning_input_packet
from future_system.reasoning_contracts.models import RenderedPromptPacket
from future_system.reasoning_contracts.renderer import render_reasoning_prompt_packet
from future_system.runtime.models import AnalysisRunError
from future_system.runtime.runner import run_analysis_pipeline
from future_system.runtime.stub_analyst import DeterministicStubAnalyst
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_RUNTIME_FIXTURE_PATH = Path("tests/fixtures/future_system/runtime/runtime_inputs.json")


def test_full_dry_run_succeeds_end_to_end_for_valid_input() -> None:
    case = _runtime_case("success_strong")
    bundle = _bundle(case["context_bundle_case"])
    analyst = DeterministicStubAnalyst()

    packet = run_analysis_pipeline(context_bundle=bundle, analyst=analyst)

    expected_reasoning_input = build_reasoning_input_packet(bundle=bundle)
    expected_prompt = render_reasoning_prompt_packet(reasoning_input=expected_reasoning_input)

    assert packet.status == case["expected_status"]
    assert packet.theme_id == bundle.theme_id
    assert packet.reasoning_input.model_dump() == expected_reasoning_input.model_dump()
    assert isinstance(packet.rendered_prompt, RenderedPromptPacket)
    assert packet.rendered_prompt.model_dump() == expected_prompt.model_dump()
    assert packet.reasoning_output.theme_id == bundle.theme_id
    assert packet.policy_decision.decision == case["expected_policy_decision"]
    assert packet.run_flags == case["expected_run_flags"]


def test_runtime_can_swap_stub_for_live_analyst_without_core_logic_rewrite() -> None:
    case = _runtime_case("success_strong")
    bundle = _bundle(case["context_bundle_case"])
    transport = _StaticTransport(
        response={"content": _valid_reasoning_output(theme_id=bundle.theme_id)}
    )
    analyst = LiveAnalystAdapter(transport=transport, timeout_seconds=1.0)

    packet = run_analysis_pipeline(context_bundle=bundle, analyst=analyst)

    assert packet.status == "success"
    assert packet.reasoning_output.theme_id == bundle.theme_id
    assert packet.policy_decision.decision == "allow"
    assert packet.run_flags == ["analysis_dry_run", "reasoning_parsed", "policy_computed"]


def test_live_analyst_transport_failure_is_distinct_from_parser_failure() -> None:
    case = _runtime_case("success_strong")
    bundle = _bundle(case["context_bundle_case"])
    analyst = LiveAnalystAdapter(
        transport=_StaticTransport(response={"choices": []}),
        timeout_seconds=1.0,
    )

    with pytest.raises(AnalysisRunError) as exc:
        run_analysis_pipeline(context_bundle=bundle, analyst=analyst)

    assert "stage=analyst_transport" in str(exc.value)
    assert "analyst_transport_failed" in str(exc.value)
    assert "reasoning_parse_failed" not in str(exc.value)


def test_live_analyst_timeout_failure_has_explicit_timeout_stage() -> None:
    case = _runtime_case("success_strong")
    bundle = _bundle(case["context_bundle_case"])
    analyst = LiveAnalystAdapter(
        transport=_TimeoutTransport(),
        timeout_seconds=0.1,
    )

    with pytest.raises(AnalysisRunError) as exc:
        run_analysis_pipeline(context_bundle=bundle, analyst=analyst)

    assert "stage=analyst_timeout" in str(exc.value)
    assert "analyst_timeout" in str(exc.value)
    assert "stage=reasoning_parse" not in str(exc.value)


def test_malformed_analyst_output_raises_analysis_run_error_deterministically() -> None:
    case = _runtime_case("malformed_analyst_output")
    bundle = _bundle(case["context_bundle_case"])
    analyst = _MalformedAnalyst(payload=case["malformed_payload"])

    with pytest.raises(AnalysisRunError) as first_exc:
        run_analysis_pipeline(context_bundle=bundle, analyst=analyst)
    with pytest.raises(AnalysisRunError) as second_exc:
        run_analysis_pipeline(context_bundle=bundle, analyst=analyst)

    assert str(first_exc.value) == str(second_exc.value)
    assert "stage=reasoning_parse" in str(first_exc.value)
    assert "reasoning_parse_failed" in str(first_exc.value)


def test_live_analyst_parser_validation_failure_remains_reasoning_parse_stage() -> None:
    case = _runtime_case("success_strong")
    bundle = _bundle(case["context_bundle_case"])
    invalid_reasoning_output = _valid_reasoning_output(theme_id=bundle.theme_id)
    invalid_reasoning_output["recommended_posture"] = "escalate"
    analyst = LiveAnalystAdapter(
        transport=_StaticTransport(response={"content": invalid_reasoning_output}),
        timeout_seconds=1.0,
    )

    with pytest.raises(AnalysisRunError) as first_exc:
        run_analysis_pipeline(context_bundle=bundle, analyst=analyst)
    with pytest.raises(AnalysisRunError) as second_exc:
        run_analysis_pipeline(context_bundle=bundle, analyst=analyst)

    assert str(first_exc.value) == str(second_exc.value)
    assert "stage=reasoning_parse" in str(first_exc.value)
    assert "reasoning_parse_failed" in str(first_exc.value)


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


def _valid_reasoning_output(*, theme_id: str) -> dict[str, object]:
    return {
        "theme_id": theme_id,
        "thesis": "Cross-market alignment supports deterministic promotion.",
        "counter_thesis": "Residual uncertainty still warrants caution.",
        "key_drivers": ["Aligned signal from candidate and comparison packets."],
        "missing_information": ["Confirm next catalyst timing."],
        "uncertainty_notes": ["Event volatility remains present."],
        "recommended_posture": "candidate",
        "confidence_explanation": "Signals are aligned with manageable conflict.",
        "analyst_flags": [],
    }


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
