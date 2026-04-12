"""Deterministic composition tests for the future_system.review_bundles surface."""

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
from future_system.runtime.runner import run_analysis_pipeline_result
from future_system.runtime.stub_analyst import DeterministicStubAnalyst
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_RUNTIME_FIXTURE_PATH = Path("tests/fixtures/future_system/runtime/runtime_inputs.json")


def test_build_review_bundle_success_composes_runtime_packet_and_renderings() -> None:
    runtime_result = run_analysis_pipeline_result(
        context_bundle=_bundle("strong_complete"),
        analyst=DeterministicStubAnalyst(),
    )

    bundle = build_review_bundle(runtime_result=runtime_result)
    payload = bundle.review_bundle

    assert bundle.status == "success"
    assert payload.bundle_kind == "analysis_success_bundle"
    assert payload.status == "success"
    assert payload.theme_id == "theme_ctx_strong"
    assert payload.run_flags == [
        "analysis_dry_run",
        "stub_analyst_used",
        "reasoning_parsed",
        "policy_computed",
    ]
    assert payload.runtime_result.status == "success"
    assert payload.review_packet.status == "success"
    assert "packet_kind=analysis_success" in payload.rendered_text
    assert "- Packet Kind: `analysis_success`" in payload.rendered_markdown
    assert (
        payload.bundle_summary
        == "theme_id=theme_ctx_strong; bundle_kind=analysis_success_bundle; status=success; "
        "run_flags=analysis_dry_run,stub_analyst_used,reasoning_parsed,policy_computed."
    )


@pytest.mark.parametrize(
    ("failure_stage", "expected_run_flags", "expected_summary"),
    [
        (
            "analyst_timeout",
            ["analysis_dry_run", "analyst_timeout"],
            "theme_id=theme_ctx_strong; bundle_kind=analysis_failure_bundle; status=failed; "
            "failure_stage=analyst_timeout; run_flags=analysis_dry_run,analyst_timeout.",
        ),
        (
            "analyst_transport",
            ["analysis_dry_run", "analyst_transport_failed"],
            "theme_id=theme_ctx_strong; bundle_kind=analysis_failure_bundle; status=failed; "
            "failure_stage=analyst_transport; "
            "run_flags=analysis_dry_run,analyst_transport_failed.",
        ),
        (
            "reasoning_parse",
            ["analysis_dry_run", "reasoning_parse_failed"],
            "theme_id=theme_ctx_strong; bundle_kind=analysis_failure_bundle; status=failed; "
            "failure_stage=reasoning_parse; run_flags=analysis_dry_run,reasoning_parse_failed.",
        ),
    ],
)
def test_build_review_bundle_failure_preserves_explicit_stage_identity(
    failure_stage: str,
    expected_run_flags: list[str],
    expected_summary: str,
) -> None:
    runtime_result = _failure_result(failure_stage)

    bundle = build_review_bundle(runtime_result=runtime_result)
    payload = bundle.review_bundle

    assert bundle.status == "failed"
    assert payload.bundle_kind == "analysis_failure_bundle"
    assert payload.status == "failed"
    assert payload.failure_stage == failure_stage
    assert payload.theme_id == "theme_ctx_strong"
    assert payload.run_flags == expected_run_flags
    assert payload.runtime_result.status == "failed"
    assert payload.review_packet.status == "failed"
    assert f"failure_stage={failure_stage}" in payload.rendered_text
    assert f"- Failure Stage: `{failure_stage}`" in payload.rendered_markdown
    assert "policy_decision=" not in payload.rendered_text
    assert payload.bundle_summary == expected_summary


def test_build_review_bundle_is_deterministic_for_same_runtime_result() -> None:
    runtime_result = run_analysis_pipeline_result(
        context_bundle=_bundle("strong_complete"),
        analyst=DeterministicStubAnalyst(),
    )

    bundle_a = build_review_bundle(runtime_result=runtime_result)
    bundle_b = build_review_bundle(runtime_result=runtime_result)

    assert bundle_a.model_dump(mode="json") == bundle_b.model_dump(mode="json")


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
