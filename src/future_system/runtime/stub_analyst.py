"""Deterministic rule-based stub analyst for offline runtime dry-run tests."""

from __future__ import annotations

import json

from future_system.reasoning_contracts.models import ReasoningInputPacket, RenderedPromptPacket
from future_system.runtime.protocol import AnalystProtocol, AnalystResponsePayload


class DeterministicStubAnalyst(AnalystProtocol):
    """Small deterministic analyst implementation with no live model transport."""

    is_stub: bool = True

    def __init__(self, *, return_json_string: bool = False) -> None:
        self._return_json_string = return_json_string

    def analyze(
        self,
        *,
        reasoning_input: ReasoningInputPacket,
        rendered_prompt: RenderedPromptPacket,
    ) -> AnalystResponsePayload:
        del rendered_prompt

        posture = _recommended_posture(reasoning_input=reasoning_input)
        analyst_flags = _analyst_flags(posture=posture)
        payload: dict[str, object] = {
            "theme_id": reasoning_input.theme_id,
            "thesis": (
                f"Deterministic stub thesis for {reasoning_input.theme_id} with posture {posture}."
            ),
            "counter_thesis": (
                "Deterministic stub counter-thesis emphasizing unresolved uncertainty."
            ),
            "key_drivers": [
                f"candidate_posture={reasoning_input.candidate_posture}",
                f"comparison_alignment={reasoning_input.comparison_alignment}",
            ],
            "missing_information": _missing_information(posture=posture),
            "uncertainty_notes": _uncertainty_notes(posture=posture),
            "recommended_posture": posture,
            "confidence_explanation": (
                "Deterministic stub confidence explanation from bounded runtime rules."
            ),
            "analyst_flags": analyst_flags,
        }

        if self._return_json_string:
            return json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return payload


def _recommended_posture(*, reasoning_input: ReasoningInputPacket) -> str:
    if (
        reasoning_input.candidate_posture == "high_conflict"
        or reasoning_input.comparison_alignment == "conflicted"
        or reasoning_input.conflict_score >= 0.70
    ):
        return "deny"
    if (
        reasoning_input.candidate_posture == "insufficient"
        or reasoning_input.comparison_alignment == "insufficient"
        or reasoning_input.confidence_score < 0.35
    ):
        return "insufficient"
    if (
        reasoning_input.candidate_posture == "candidate"
        and reasoning_input.comparison_alignment == "aligned"
        and reasoning_input.candidate_score >= 0.65
    ):
        return "candidate"
    return "watch"


def _missing_information(*, posture: str) -> list[str]:
    if posture == "candidate":
        return ["Confirm next official catalyst timing."]
    if posture == "watch":
        return ["Gather more directional confirmation.", "Await fresher contextual evidence."]
    if posture == "insufficient":
        return [
            "Collect complete probability inputs.",
            "Collect secondary source confirmation.",
        ]
    return [
        "Resolve cross-market directional conflict.",
        "Verify conflict drivers with updated snapshots.",
        "Confirm independent supporting context.",
    ]


def _uncertainty_notes(*, posture: str) -> list[str]:
    if posture == "candidate":
        return ["Residual event-risk remains."]
    if posture == "watch":
        return ["Signal remains directionally tentative."]
    if posture == "insufficient":
        return ["Current context lacks sufficient confidence for promotion."]
    return ["Conflict uncertainty dominates current setup."]


def _analyst_flags(*, posture: str) -> list[str]:
    if posture == "deny":
        return ["policy_blocker", "reasoning_posture_deny"]
    if posture == "insufficient":
        return ["reasoning_posture_insufficient"]
    return []
