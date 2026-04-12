"""Engine behavior tests for deterministic policy decisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from future_system.context_bundle.models import OpportunityContextBundle
from future_system.policy_engine.engine import evaluate_policy_decision
from future_system.policy_engine.models import PolicyDecisionError
from future_system.reasoning_contracts.models import ReasoningOutputPacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/policy/policy_inputs.json")


def test_matching_theme_ids_are_required() -> None:
    case = _case("allow")
    bundle = OpportunityContextBundle.model_validate(case["context_bundle"])
    reasoning = ReasoningOutputPacket.model_validate(case["reasoning_output"]).model_copy(
        update={"theme_id": "theme_mismatch"}
    )

    with pytest.raises(PolicyDecisionError, match="theme_id_mismatch"):
        evaluate_policy_decision(context_bundle=bundle, reasoning_output=reasoning)


@pytest.mark.parametrize(
    ("case_name", "expected_decision"),
    [("allow", "allow"), ("hold", "hold"), ("deny", "deny")],
)
def test_policy_engine_classifies_allow_hold_deny_cases(
    case_name: str,
    expected_decision: str,
) -> None:
    packet = _evaluate_case(case_name)

    assert packet.decision == expected_decision
    assert 0.0 <= packet.decision_score <= 1.0
    assert 0.0 <= packet.readiness_score <= 1.0
    assert 0.0 <= packet.risk_penalty <= 1.0


def test_reason_codes_and_summary_are_deterministic() -> None:
    first = _evaluate_case("hold")
    second = _evaluate_case("hold")

    assert first.reason_codes == second.reason_codes == [
        "reasoning_supportive",
        "insufficient_news_support",
        "stale_context",
        "bundle_incomplete",
    ]
    assert first.summary == second.summary
    assert (
        first.summary
        == "theme_id=theme_ctx_weak; decision=hold; decision_score=0.258; "
        "readiness_score=0.416; risk_penalty=0.551; "
        "reasons=reasoning_supportive,insufficient_news_support,stale_context,bundle_incomplete."
    )


def test_important_bundle_and_reasoning_flags_propagate() -> None:
    packet = _evaluate_case("deny")

    assert packet.flags == [
        "cross_market_conflict",
        "high_internal_divergence",
        "policy_blocker",
        "reasoning_posture_deny",
    ]


def _evaluate_case(case_name: str) -> Any:
    case = _case(case_name)
    context_bundle = OpportunityContextBundle.model_validate(case["context_bundle"])
    reasoning_output = ReasoningOutputPacket.model_validate(case["reasoning_output"])
    return evaluate_policy_decision(
        context_bundle=context_bundle,
        reasoning_output=reasoning_output,
    )


def _case(case_name: str) -> dict[str, Any]:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    for item in payload:
        if item["case"] == case_name:
            return dict(item)
    raise AssertionError(f"Missing policy fixture case: {case_name}")
