"""Renderer behavior tests for deterministic reasoning contract prompts."""

from __future__ import annotations

import json
from pathlib import Path

from future_system.reasoning_contracts.models import ReasoningInputPacket
from future_system.reasoning_contracts.renderer import (
    render_reasoning_output_schema,
    render_reasoning_prompt_packet,
)

_FIXTURE_PATH = Path("tests/fixtures/future_system/reasoning/reasoning_inputs.json")


def test_rendered_prompts_are_deterministic() -> None:
    reasoning_input = _input_packet("strong_complete")

    first = render_reasoning_prompt_packet(reasoning_input=reasoning_input)
    second = render_reasoning_prompt_packet(reasoning_input=reasoning_input)

    assert first.model_dump() == second.model_dump()


def test_rendered_prompts_include_key_fields() -> None:
    reasoning_input = _input_packet("strong_complete")

    rendered = render_reasoning_prompt_packet(reasoning_input=reasoning_input)

    assert "theme_id=theme_ctx_strong" in rendered.user_prompt
    assert "candidate_posture=candidate" in rendered.user_prompt
    assert "comparison_alignment=aligned" in rendered.user_prompt
    assert "structured_facts=" in rendered.user_prompt


def test_rendered_json_schema_is_deterministic() -> None:
    reasoning_input = _input_packet("strong_complete")

    rendered = render_reasoning_prompt_packet(reasoning_input=reasoning_input)
    schema = render_reasoning_output_schema()

    assert rendered.rendered_json_schema == schema
    assert schema["required"] == [
        "theme_id",
        "thesis",
        "counter_thesis",
        "key_drivers",
        "missing_information",
        "uncertainty_notes",
        "recommended_posture",
        "confidence_explanation",
        "analyst_flags",
    ]


def test_system_and_user_prompts_are_stable_for_known_input() -> None:
    reasoning_input = _input_packet("strong_complete")

    rendered = render_reasoning_prompt_packet(reasoning_input=reasoning_input)

    assert rendered.system_prompt == (
        "You are a cautious market analyst. Use only the provided deterministic facts. "
        "Do not invent data. Do not claim certainty. Return strict JSON only that matches "
        "the required output schema."
    )
    assert rendered.user_prompt == (
        "Analyze the following opportunity context and return strict JSON.\n"
        "theme_id=theme_ctx_strong\n"
        "title=Crypto Regulation Signal\n"
        "candidate_posture=candidate\n"
        "comparison_alignment=aligned\n"
        "candidate_score=0.840\n"
        "confidence_score=0.860\n"
        "conflict_score=0.120\n"
        "bundle_flags=[]\n"
        "operator_summary=theme_id=theme_ctx_strong; posture=candidate; alignment=aligned; "
        "completeness=1.000; freshness=0.870; confidence=0.859; conflict=0.127; flags=none.\n"
        "structured_facts={\"bundle_completeness_score\":1.0,\"bundle_key_flags\":[],"
        "\"candidate_posture\":\"candidate\",\"candidate_score\":0.84,"
        "\"comparison_alignment\":\"aligned\",\"confidence_score\":0.86,"
        "\"conflict_score\":0.12,\"news_matched_article_count\":2,"
        "\"news_official_source_present\":true,"
        "\"primary_market_slug\":\"crypto-regulation-signal\","
        "\"primary_symbol\":\"BTC-PERP\"}\n"
        "Required output fields: thesis, counter_thesis, key_drivers, missing_information, "
        "uncertainty_notes, recommended_posture, confidence_explanation, analyst_flags.\n"
        "Return only JSON object with no markdown and no extra text."
    )


def _input_packet(case_name: str) -> ReasoningInputPacket:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    for item in payload:
        if item["case"] == case_name:
            return ReasoningInputPacket.model_validate(item["input_packet"])
    raise AssertionError(f"Missing reasoning input fixture case: {case_name}")
