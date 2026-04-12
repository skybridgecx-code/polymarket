"""Deterministic behavior tests for runtime stub analyst."""

from __future__ import annotations

from future_system.reasoning_contracts.models import ReasoningInputPacket
from future_system.reasoning_contracts.parser import parse_reasoning_output
from future_system.reasoning_contracts.renderer import render_reasoning_prompt_packet
from future_system.runtime.stub_analyst import DeterministicStubAnalyst


def test_stub_analyst_returns_deterministic_payload_for_known_input() -> None:
    reasoning_input = _reasoning_input(
        candidate_posture="candidate",
        comparison_alignment="aligned",
        candidate_score=0.84,
        confidence_score=0.86,
        conflict_score=0.12,
    )
    rendered_prompt = render_reasoning_prompt_packet(reasoning_input=reasoning_input)
    analyst = DeterministicStubAnalyst()

    output_a = analyst.analyze(reasoning_input=reasoning_input, rendered_prompt=rendered_prompt)
    output_b = analyst.analyze(reasoning_input=reasoning_input, rendered_prompt=rendered_prompt)

    assert output_a == output_b


def test_stub_output_shape_is_parseable_by_reasoning_parser() -> None:
    reasoning_input = _reasoning_input(
        candidate_posture="candidate",
        comparison_alignment="aligned",
        candidate_score=0.84,
        confidence_score=0.86,
        conflict_score=0.12,
    )
    rendered_prompt = render_reasoning_prompt_packet(reasoning_input=reasoning_input)
    analyst = DeterministicStubAnalyst(return_json_string=True)

    output_payload = analyst.analyze(
        reasoning_input=reasoning_input,
        rendered_prompt=rendered_prompt,
    )
    parsed = parse_reasoning_output(output_payload)

    assert parsed.theme_id == "theme_runtime_stub"
    assert parsed.recommended_posture == "candidate"


def test_known_input_state_changes_produce_deterministic_posture_differences() -> None:
    candidate_input = _reasoning_input(
        candidate_posture="candidate",
        comparison_alignment="aligned",
        candidate_score=0.84,
        confidence_score=0.86,
        conflict_score=0.12,
    )
    deny_input = _reasoning_input(
        candidate_posture="high_conflict",
        comparison_alignment="conflicted",
        candidate_score=0.46,
        confidence_score=0.52,
        conflict_score=0.81,
    )
    insufficient_input = _reasoning_input(
        candidate_posture="insufficient",
        comparison_alignment="insufficient",
        candidate_score=0.31,
        confidence_score=0.29,
        conflict_score=0.43,
    )
    analyst = DeterministicStubAnalyst()

    candidate_output = parse_reasoning_output(
        analyst.analyze(
            reasoning_input=candidate_input,
            rendered_prompt=render_reasoning_prompt_packet(reasoning_input=candidate_input),
        )
    )
    deny_output = parse_reasoning_output(
        analyst.analyze(
            reasoning_input=deny_input,
            rendered_prompt=render_reasoning_prompt_packet(reasoning_input=deny_input),
        )
    )
    insufficient_output = parse_reasoning_output(
        analyst.analyze(
            reasoning_input=insufficient_input,
            rendered_prompt=render_reasoning_prompt_packet(reasoning_input=insufficient_input),
        )
    )

    assert candidate_output.recommended_posture == "candidate"
    assert deny_output.recommended_posture == "deny"
    assert insufficient_output.recommended_posture == "insufficient"


def _reasoning_input(
    *,
    candidate_posture: str,
    comparison_alignment: str,
    candidate_score: float,
    confidence_score: float,
    conflict_score: float,
) -> ReasoningInputPacket:
    return ReasoningInputPacket.model_validate(
        {
            "theme_id": "theme_runtime_stub",
            "title": "Runtime Stub Fixture",
            "candidate_posture": candidate_posture,
            "comparison_alignment": comparison_alignment,
            "candidate_score": candidate_score,
            "confidence_score": confidence_score,
            "conflict_score": conflict_score,
            "bundle_flags": [],
            "operator_summary": "Deterministic runtime stub operator summary.",
            "structured_facts": {
                "candidate_posture": candidate_posture,
                "comparison_alignment": comparison_alignment,
                "candidate_score": candidate_score,
                "confidence_score": confidence_score,
                "conflict_score": conflict_score,
                "primary_market_slug": "runtime-stub-market",
                "primary_symbol": "BTC-PERP",
                "news_matched_article_count": 1,
                "news_official_source_present": True,
                "bundle_completeness_score": 0.82,
                "bundle_key_flags": [],
            },
            "prompt_version": "v1",
        }
    )
