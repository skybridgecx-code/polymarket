"""Deterministic prompt renderer for reasoning contracts."""

from __future__ import annotations

import json

from future_system.reasoning_contracts.models import (
    ReasoningInputPacket,
    RenderedPromptPacket,
)

_SYSTEM_PROMPT = (
    "You are a cautious market analyst. Use only the provided deterministic facts. "
    "Do not invent data. Do not claim certainty. Return strict JSON only that matches "
    "the required output schema."
)


def render_reasoning_prompt_packet(
    *,
    reasoning_input: ReasoningInputPacket,
) -> RenderedPromptPacket:
    """Render a deterministic system/user prompt pair and output schema contract."""

    schema = render_reasoning_output_schema()
    user_prompt = _render_user_prompt(reasoning_input=reasoning_input)

    return RenderedPromptPacket(
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        rendered_json_schema=schema,
    )


def render_reasoning_output_schema() -> dict[str, object]:
    """Return a stable JSON-schema-like shape for ReasoningOutputPacket."""

    return {
        "type": "object",
        "required": [
            "theme_id",
            "thesis",
            "counter_thesis",
            "key_drivers",
            "missing_information",
            "uncertainty_notes",
            "recommended_posture",
            "confidence_explanation",
            "analyst_flags",
        ],
        "properties": {
            "theme_id": {"type": "string"},
            "thesis": {"type": "string"},
            "counter_thesis": {"type": "string"},
            "key_drivers": {"type": "array", "items": {"type": "string"}},
            "missing_information": {"type": "array", "items": {"type": "string"}},
            "uncertainty_notes": {"type": "array", "items": {"type": "string"}},
            "recommended_posture": {
                "type": "string",
                "enum": [
                    "watch",
                    "candidate",
                    "high_conflict",
                    "deny",
                    "insufficient",
                ],
            },
            "confidence_explanation": {"type": "string"},
            "analyst_flags": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }


def _render_user_prompt(*, reasoning_input: ReasoningInputPacket) -> str:
    structured_facts_json = json.dumps(
        reasoning_input.structured_facts,
        sort_keys=True,
        separators=(",", ":"),
    )
    bundle_flags_json = json.dumps(reasoning_input.bundle_flags, separators=(",", ":"))

    return (
        "Analyze the following opportunity context and return strict JSON.\n"
        f"theme_id={reasoning_input.theme_id}\n"
        f"title={reasoning_input.title or 'none'}\n"
        f"candidate_posture={reasoning_input.candidate_posture}\n"
        f"comparison_alignment={reasoning_input.comparison_alignment}\n"
        f"candidate_score={reasoning_input.candidate_score:.3f}\n"
        f"confidence_score={reasoning_input.confidence_score:.3f}\n"
        f"conflict_score={reasoning_input.conflict_score:.3f}\n"
        f"bundle_flags={bundle_flags_json}\n"
        f"operator_summary={reasoning_input.operator_summary}\n"
        f"structured_facts={structured_facts_json}\n"
        "Required output fields: thesis, counter_thesis, key_drivers, "
        "missing_information, uncertainty_notes, recommended_posture, "
        "confidence_explanation, analyst_flags.\n"
        "Return only JSON object with no markdown and no extra text."
    )
