"""Model validation tests for future_system.policy_engine contracts."""

from __future__ import annotations

import pytest
from future_system.policy_engine.models import PolicyDecisionPacket
from pydantic import ValidationError


def test_policy_decision_models_accept_valid_payloads() -> None:
    packet = PolicyDecisionPacket.model_validate(
        {
            "theme_id": "theme_policy_valid",
            "decision": "allow",
            "decision_score": 0.82,
            "readiness_score": 0.77,
            "risk_penalty": 0.21,
            "reason_codes": ["strong_candidate_alignment", "reasoning_supportive"],
            "flags": ["context_incomplete", "stale_context"],
            "summary": (
                "theme_id=theme_policy_valid; decision=allow; decision_score=0.820; "
                "readiness_score=0.770; risk_penalty=0.210; "
                "reasons=strong_candidate_alignment,reasoning_supportive."
            ),
        }
    )

    assert packet.theme_id == "theme_policy_valid"
    assert packet.decision == "allow"
    assert packet.reason_codes == ["strong_candidate_alignment", "reasoning_supportive"]


@pytest.mark.parametrize("field_name", ["decision_score", "readiness_score", "risk_penalty"])
def test_invalid_bounded_scores_are_rejected(field_name: str) -> None:
    payload: dict[str, object] = {
        "theme_id": "theme_policy_invalid",
        "decision": "hold",
        "decision_score": 0.5,
        "readiness_score": 0.5,
        "risk_penalty": 0.5,
        "reason_codes": ["bundle_incomplete"],
        "flags": [],
        "summary": "deterministic summary",
    }
    payload[field_name] = 1.4

    with pytest.raises(ValidationError):
        PolicyDecisionPacket.model_validate(payload)


def test_invalid_decision_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PolicyDecisionPacket.model_validate(
            {
                "theme_id": "theme_policy_invalid",
                "decision": "approve",
                "decision_score": 0.6,
                "readiness_score": 0.6,
                "risk_penalty": 0.3,
                "reason_codes": ["reasoning_supportive"],
                "flags": [],
                "summary": "invalid decision payload",
            }
        )
