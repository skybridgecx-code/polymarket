"""Deterministic policy decision engine over context bundles and reasoning outputs."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.policy_engine.models import (
    PolicyDecisionError,
    PolicyDecisionPacket,
)
from future_system.policy_engine.scoring import (
    classify_policy_decision,
    compute_policy_decision_score,
    compute_policy_readiness_score,
    compute_policy_risk_penalty,
    derive_policy_reason_codes,
)
from future_system.reasoning_contracts.models import ReasoningOutputPacket

_IMPORTANT_BUNDLE_FLAGS = frozenset(
    {
        "context_incomplete",
        "stale_context",
        "weak_news_context",
        "weak_crypto_context",
        "cross_market_conflict",
        "high_internal_divergence",
        "candidate_insufficient",
    }
)
_IMPORTANT_REASONING_FLAGS = frozenset(
    {
        "reasoning_high_conflict",
        "reasoning_posture_deny",
        "reasoning_posture_insufficient",
        "missing_information_significant",
        "escalate_conflict_review",
        "policy_blocker",
    }
)


def evaluate_policy_decision(
    *,
    context_bundle: OpportunityContextBundle,
    reasoning_output: ReasoningOutputPacket,
) -> PolicyDecisionPacket:
    """Evaluate deterministic policy decision from one bundle and reasoning output."""

    if context_bundle.theme_id != reasoning_output.theme_id:
        raise PolicyDecisionError(
            "theme_id_mismatch: "
            f"bundle={context_bundle.theme_id!r} reasoning={reasoning_output.theme_id!r}"
        )

    missing_information_count = len(reasoning_output.missing_information)
    uncertainty_count = len(reasoning_output.uncertainty_notes)

    readiness_score = compute_policy_readiness_score(
        completeness_score=context_bundle.quality.completeness_score,
        freshness_score=context_bundle.quality.freshness_score,
        confidence_score=context_bundle.quality.confidence_score,
        missing_information_count=missing_information_count,
        uncertainty_count=uncertainty_count,
    )
    risk_penalty = compute_policy_risk_penalty(
        bundle_conflict_score=context_bundle.quality.conflict_score,
        candidate_conflict_score=context_bundle.candidate.conflict_score,
        comparison_alignment=context_bundle.comparison.alignment,
        reasoning_posture=reasoning_output.recommended_posture,
        missing_information_count=missing_information_count,
        uncertainty_count=uncertainty_count,
        flags=context_bundle.flags,
    )
    decision_score = compute_policy_decision_score(
        candidate_score=context_bundle.candidate.candidate_score,
        bundle_confidence_score=context_bundle.quality.confidence_score,
        readiness_score=readiness_score,
        risk_penalty=risk_penalty,
        comparison_alignment=context_bundle.comparison.alignment,
        reasoning_posture=reasoning_output.recommended_posture,
        flags=context_bundle.flags,
    )

    decision = classify_policy_decision(
        decision_score=decision_score,
        readiness_score=readiness_score,
        risk_penalty=risk_penalty,
        reasoning_posture=reasoning_output.recommended_posture,
        comparison_alignment=context_bundle.comparison.alignment,
    )

    propagated_flags = _derive_policy_flags(
        bundle_flags=context_bundle.flags,
        reasoning_flags=reasoning_output.analyst_flags,
    )
    reason_codes = derive_policy_reason_codes(
        candidate_score=context_bundle.candidate.candidate_score,
        bundle_confidence_score=context_bundle.quality.confidence_score,
        bundle_conflict_score=context_bundle.quality.conflict_score,
        candidate_posture=context_bundle.candidate.posture,
        comparison_alignment=context_bundle.comparison.alignment,
        reasoning_posture=reasoning_output.recommended_posture,
        missing_information_count=missing_information_count,
        flags=propagated_flags,
    )

    summary = _build_summary(
        theme_id=context_bundle.theme_id,
        decision=decision,
        decision_score=decision_score,
        readiness_score=readiness_score,
        risk_penalty=risk_penalty,
        reason_codes=reason_codes,
    )

    return PolicyDecisionPacket(
        theme_id=context_bundle.theme_id,
        decision=decision,
        decision_score=decision_score,
        readiness_score=readiness_score,
        risk_penalty=risk_penalty,
        reason_codes=reason_codes,
        flags=propagated_flags,
        summary=summary,
    )


def _derive_policy_flags(*, bundle_flags: list[str], reasoning_flags: list[str]) -> list[str]:
    flags: list[str] = []

    for flag in bundle_flags:
        if flag not in _IMPORTANT_BUNDLE_FLAGS:
            continue
        if flag in flags:
            continue
        flags.append(flag)

    for flag in reasoning_flags:
        if flag not in _IMPORTANT_REASONING_FLAGS:
            continue
        if flag in flags:
            continue
        flags.append(flag)

    return flags


def _build_summary(
    *,
    theme_id: str,
    decision: str,
    decision_score: float,
    readiness_score: float,
    risk_penalty: float,
    reason_codes: Sequence[str],
) -> str:
    reasons_text = "none" if not reason_codes else ",".join(reason_codes[:4])
    return (
        f"theme_id={theme_id}; "
        f"decision={decision}; "
        f"decision_score={decision_score:.3f}; "
        f"readiness_score={readiness_score:.3f}; "
        f"risk_penalty={risk_penalty:.3f}; "
        f"reasons={reasons_text}."
    )
