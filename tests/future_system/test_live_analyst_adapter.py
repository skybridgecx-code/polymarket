"""Unit tests for bounded live analyst transport adapter behavior."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest
from future_system.live_analyst.adapter import LiveAnalystAdapter
from future_system.live_analyst.errors import LiveAnalystTimeoutError, LiveAnalystTransportError
from future_system.live_analyst.models import LiveAnalystTransportRequest
from future_system.reasoning_contracts.models import ReasoningInputPacket
from future_system.reasoning_contracts.parser import parse_reasoning_output
from future_system.reasoning_contracts.renderer import render_reasoning_prompt_packet


def test_live_analyst_successfully_returns_parseable_model_content() -> None:
    reasoning_input = _reasoning_input()
    rendered_prompt = render_reasoning_prompt_packet(reasoning_input=reasoning_input)
    transport = _RecordingTransport(
        response={
            "content": _valid_reasoning_output(theme_id=reasoning_input.theme_id),
        }
    )
    analyst = LiveAnalystAdapter(
        transport=transport,
        timeout_seconds=2.0,
        model="gpt-4.1-mini",
    )

    payload = analyst.analyze(
        reasoning_input=reasoning_input,
        rendered_prompt=rendered_prompt,
    )
    parsed = parse_reasoning_output(payload)

    assert parsed.theme_id == "theme_live_analyst"
    assert parsed.recommended_posture == "candidate"
    assert len(transport.requests) == 1
    assert transport.requests[0].input_mode == "rendered_prompt"
    assert transport.requests[0].metadata == {
        "theme_id": "theme_live_analyst",
        "prompt_version": "v1",
    }
    assert transport.requests[0].model == "gpt-4.1-mini"


@pytest.mark.parametrize(
    ("rendered_prompt", "expected_input_mode"),
    [
        (None, "reasoning_input"),
        ("Return strict JSON only.", "rendered_prompt_text"),
    ],
)
def test_live_analyst_accepts_reasoning_input_or_prompt_string(
    rendered_prompt: str | None,
    expected_input_mode: str,
) -> None:
    reasoning_input = _reasoning_input()
    transport = _RecordingTransport(
        response={
            "content": _valid_reasoning_output(theme_id=reasoning_input.theme_id),
        }
    )
    analyst = LiveAnalystAdapter(transport=transport, timeout_seconds=1.0)

    _ = analyst.analyze_request(
        reasoning_input=reasoning_input,
        rendered_prompt=rendered_prompt,
    )

    assert len(transport.requests) == 1
    assert transport.requests[0].input_mode == expected_input_mode


def test_live_analyst_malformed_transport_response_raises_transport_error() -> None:
    reasoning_input = _reasoning_input()
    rendered_prompt = render_reasoning_prompt_packet(reasoning_input=reasoning_input)
    transport = _RecordingTransport(response={"choices": []})
    analyst = LiveAnalystAdapter(transport=transport, timeout_seconds=1.0)

    with pytest.raises(LiveAnalystTransportError, match="invalid_response"):
        analyst.analyze(
            reasoning_input=reasoning_input,
            rendered_prompt=rendered_prompt,
        )


def test_live_analyst_timeout_raises_explicit_timeout_error() -> None:
    reasoning_input = _reasoning_input()
    rendered_prompt = render_reasoning_prompt_packet(reasoning_input=reasoning_input)
    transport = _TimeoutTransport()
    analyst = LiveAnalystAdapter(transport=transport, timeout_seconds=0.2)

    with pytest.raises(LiveAnalystTimeoutError, match="live_analyst_timeout"):
        analyst.analyze(
            reasoning_input=reasoning_input,
            rendered_prompt=rendered_prompt,
        )


class _RecordingTransport:
    def __init__(self, *, response: Mapping[str, Any] | str) -> None:
        self._response = response
        self.requests: list[LiveAnalystTransportRequest] = []

    def request(self, *, request: LiveAnalystTransportRequest) -> Mapping[str, Any] | str:
        self.requests.append(request)
        return self._response


class _TimeoutTransport:
    def request(self, *, request: LiveAnalystTransportRequest) -> Mapping[str, Any] | str:
        del request
        raise TimeoutError("simulated timeout")


def _reasoning_input() -> ReasoningInputPacket:
    return ReasoningInputPacket.model_validate(
        {
            "theme_id": "theme_live_analyst",
            "title": "Live Analyst Fixture",
            "candidate_posture": "candidate",
            "comparison_alignment": "aligned",
            "candidate_score": 0.82,
            "confidence_score": 0.81,
            "conflict_score": 0.15,
            "bundle_flags": [],
            "operator_summary": "Deterministic live analyst fixture summary.",
            "structured_facts": {
                "candidate_posture": "candidate",
                "comparison_alignment": "aligned",
                "candidate_score": 0.82,
                "confidence_score": 0.81,
                "conflict_score": 0.15,
                "primary_market_slug": "live-analyst-fixture",
                "primary_symbol": "BTC-PERP",
                "news_matched_article_count": 2,
                "news_official_source_present": True,
                "bundle_completeness_score": 0.91,
                "bundle_key_flags": [],
            },
            "prompt_version": "v1",
        }
    )


def _valid_reasoning_output(*, theme_id: str) -> dict[str, object]:
    return {
        "theme_id": theme_id,
        "thesis": "Deterministic live analyst thesis with supportive cross-market alignment.",
        "counter_thesis": "Residual event-risk still warrants measured caution.",
        "key_drivers": ["Candidate score remains supportive."],
        "missing_information": ["Await next official macro release."],
        "uncertainty_notes": ["Positioning can reverse quickly."],
        "recommended_posture": "candidate",
        "confidence_explanation": "Evidence quality and alignment are currently supportive.",
        "analyst_flags": [],
    }
