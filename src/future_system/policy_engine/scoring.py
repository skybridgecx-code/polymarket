"""Deterministic scoring helpers for context+reasoning policy decisions."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.policy_engine.models import PolicyDecisionAction, PolicyReasonCode


def compute_policy_readiness_score(
    *,
    completeness_score: float,
    freshness_score: float,
    confidence_score: float,
    missing_information_count: int,
    uncertainty_count: int,
) -> float:
    """Compute bounded readiness from context quality plus reasoning gaps."""

    base_score = (
        0.45 * clamp_unit(completeness_score)
        + 0.25 * clamp_unit(freshness_score)
        + 0.30 * clamp_unit(confidence_score)
    )

    penalty = 0.0
    penalty += min(0.20, 0.04 * max(missing_information_count, 0))
    penalty += min(0.12, 0.03 * max(uncertainty_count, 0))
    return round(clamp_unit(base_score - penalty), 3)


def compute_policy_risk_penalty(
    *,
    bundle_conflict_score: float,
    candidate_conflict_score: float,
    comparison_alignment: str,
    reasoning_posture: str,
    missing_information_count: int,
    uncertainty_count: int,
    flags: Sequence[str],
) -> float:
    """Compute bounded risk penalty from conflict signals and negative reasoning factors."""

    alignment_component = {
        "aligned": 0.05,
        "weakly_aligned": 0.25,
        "insufficient": 0.45,
        "conflicted": 0.90,
    }.get(comparison_alignment, 0.45)
    reasoning_component = {
        "candidate": 0.05,
        "watch": 0.20,
        "insufficient": 0.45,
        "high_conflict": 0.80,
        "deny": 1.00,
    }.get(reasoning_posture, 0.45)

    raw = (
        0.40 * clamp_unit(bundle_conflict_score)
        + 0.25 * clamp_unit(candidate_conflict_score)
        + 0.20 * alignment_component
        + 0.15 * reasoning_component
    )

    raw += min(0.15, 0.04 * max(missing_information_count, 0))
    raw += min(0.10, 0.03 * max(uncertainty_count, 0))

    flag_set = set(flags)
    if "cross_market_conflict" in flag_set or "high_internal_divergence" in flag_set:
        raw += 0.08
    if "stale_context" in flag_set:
        raw += 0.05

    return round(clamp_unit(raw), 3)


def compute_policy_decision_score(
    *,
    candidate_score: float,
    bundle_confidence_score: float,
    readiness_score: float,
    risk_penalty: float,
    comparison_alignment: str,
    reasoning_posture: str,
    flags: Sequence[str],
) -> float:
    """Compute bounded decision score from quality, readiness, and risk signals."""

    alignment_adjustment = {
        "aligned": 0.10,
        "weakly_aligned": 0.04,
        "insufficient": -0.08,
        "conflicted": -0.20,
    }.get(comparison_alignment, -0.08)
    posture_adjustment = {
        "candidate": 0.10,
        "watch": 0.03,
        "insufficient": -0.12,
        "high_conflict": -0.25,
        "deny": -0.35,
    }.get(reasoning_posture, -0.12)

    raw = (
        0.40 * clamp_unit(candidate_score)
        + 0.25 * clamp_unit(bundle_confidence_score)
        + 0.35 * clamp_unit(readiness_score)
    )
    raw += alignment_adjustment + posture_adjustment
    raw -= 0.45 * clamp_unit(risk_penalty)

    flag_set = set(flags)
    if "context_incomplete" in flag_set:
        raw -= 0.05
    if "stale_context" in flag_set:
        raw -= 0.05

    return round(clamp_unit(raw), 3)


def classify_policy_decision(
    *,
    decision_score: float,
    readiness_score: float,
    risk_penalty: float,
    reasoning_posture: str,
    comparison_alignment: str,
) -> PolicyDecisionAction:
    """Classify final deterministic policy action from thresholded score signals."""

    if reasoning_posture == "deny":
        return "deny"
    if reasoning_posture == "high_conflict":
        return "deny"
    if comparison_alignment == "conflicted" and risk_penalty >= 0.55:
        return "deny"

    if (
        decision_score >= 0.68
        and readiness_score >= 0.60
        and risk_penalty <= 0.45
        and reasoning_posture not in {"insufficient"}
    ):
        return "allow"

    if decision_score < 0.22 or readiness_score < 0.22 or risk_penalty >= 0.80:
        return "deny"

    return "hold"


def derive_policy_reason_codes(
    *,
    candidate_score: float,
    bundle_confidence_score: float,
    bundle_conflict_score: float,
    candidate_posture: str,
    comparison_alignment: str,
    reasoning_posture: str,
    missing_information_count: int,
    flags: Sequence[str],
) -> list[PolicyReasonCode]:
    """Derive deterministic concise reason codes from bundle and reasoning state."""

    reason_codes: list[PolicyReasonCode] = []
    flag_set = set(flags)

    if candidate_score >= 0.70 and comparison_alignment == "aligned":
        _append_reason(reason_codes, "strong_candidate_alignment")
    if reasoning_posture in {"candidate", "watch"} and missing_information_count <= 2:
        _append_reason(reason_codes, "reasoning_supportive")
    if candidate_score < 0.45:
        _append_reason(reason_codes, "weak_candidate_score")
    if bundle_confidence_score < 0.50:
        _append_reason(reason_codes, "weak_confidence")
    if bundle_conflict_score >= 0.65:
        _append_reason(reason_codes, "high_conflict")
    if candidate_posture == "insufficient":
        _append_reason(reason_codes, "candidate_insufficient")
    if comparison_alignment == "conflicted":
        _append_reason(reason_codes, "comparison_conflicted")
    if reasoning_posture == "high_conflict":
        _append_reason(reason_codes, "reasoning_high_conflict")
    if missing_information_count >= 3:
        _append_reason(reason_codes, "missing_information_significant")
    if "weak_news_context" in flag_set:
        _append_reason(reason_codes, "insufficient_news_support")
    if "stale_context" in flag_set:
        _append_reason(reason_codes, "stale_context")
    if "context_incomplete" in flag_set:
        _append_reason(reason_codes, "bundle_incomplete")
    if reasoning_posture == "deny":
        _append_reason(reason_codes, "reasoning_posture_deny")
    if reasoning_posture == "insufficient":
        _append_reason(reason_codes, "reasoning_posture_insufficient")

    return reason_codes


def _append_reason(
    reason_codes: list[PolicyReasonCode],
    reason: PolicyReasonCode,
    *,
    max_reasons: int = 6,
) -> None:
    if len(reason_codes) >= max_reasons:
        return
    if reason in reason_codes:
        return
    reason_codes.append(reason)


def clamp_unit(value: float) -> float:
    """Clamp numeric values into the closed unit interval."""

    return max(0.0, min(1.0, value))
