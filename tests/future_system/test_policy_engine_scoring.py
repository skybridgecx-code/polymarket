"""Scoring tests for deterministic policy engine helpers."""

from __future__ import annotations

from future_system.policy_engine.scoring import (
    classify_policy_decision,
    compute_policy_decision_score,
    compute_policy_readiness_score,
    compute_policy_risk_penalty,
)


def test_policy_decision_score_is_bounded_in_unit_interval() -> None:
    score = compute_policy_decision_score(
        candidate_score=2.0,
        bundle_confidence_score=-2.0,
        readiness_score=2.0,
        risk_penalty=-1.0,
        comparison_alignment="conflicted",
        reasoning_posture="deny",
        flags=["context_incomplete", "stale_context"],
    )

    assert 0.0 <= score <= 1.0


def test_policy_readiness_score_is_bounded_in_unit_interval() -> None:
    score = compute_policy_readiness_score(
        completeness_score=2.0,
        freshness_score=-1.0,
        confidence_score=2.0,
        missing_information_count=20,
        uncertainty_count=20,
    )

    assert 0.0 <= score <= 1.0


def test_policy_risk_penalty_is_bounded_in_unit_interval() -> None:
    penalty = compute_policy_risk_penalty(
        bundle_conflict_score=2.0,
        candidate_conflict_score=-2.0,
        comparison_alignment="conflicted",
        reasoning_posture="deny",
        missing_information_count=20,
        uncertainty_count=20,
        flags=["cross_market_conflict", "high_internal_divergence", "stale_context"],
    )

    assert 0.0 <= penalty <= 1.0


def test_explicit_threshold_inputs_yield_deterministic_allow_hold_deny() -> None:
    allow = classify_policy_decision(
        decision_score=0.74,
        readiness_score=0.68,
        risk_penalty=0.33,
        reasoning_posture="candidate",
        comparison_alignment="aligned",
    )
    hold = classify_policy_decision(
        decision_score=0.38,
        readiness_score=0.44,
        risk_penalty=0.54,
        reasoning_posture="watch",
        comparison_alignment="weakly_aligned",
    )
    deny = classify_policy_decision(
        decision_score=0.9,
        readiness_score=0.9,
        risk_penalty=0.1,
        reasoning_posture="deny",
        comparison_alignment="aligned",
    )

    assert allow == "allow"
    assert hold == "hold"
    assert deny == "deny"
