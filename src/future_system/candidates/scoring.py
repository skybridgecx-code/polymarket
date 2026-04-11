"""Deterministic scoring helpers for candidate signal construction."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.candidates.models import CandidatePosture, CandidateReasonCode

_STALE_FLAGS = frozenset(
    {
        "stale_snapshot",
        "stale_evidence",
        "stale_polymarket_evidence",
        "stale_crypto_evidence",
    }
)
_MISSING_PROBABILITY_FLAGS = frozenset(
    {
        "missing_probability_inputs",
        "missing_implied_probability",
        "no_aggregate_probability",
        "polymarket_unknown_direction",
    }
)


def compute_candidate_score(
    *,
    agreement_score: float,
    comparison_confidence: float,
    evidence_score: float,
    evidence_liquidity: float,
    evidence_freshness: float,
    crypto_coverage: float,
    crypto_liquidity: float,
    crypto_freshness: float,
    divergence_score: float,
    alignment: str,
    flags: Sequence[str],
) -> float:
    """Compute bounded candidate strength from upstream alignment and quality signals."""

    market_quality = clamp_unit((evidence_score + evidence_liquidity + evidence_freshness) / 3.0)
    crypto_quality = clamp_unit((crypto_coverage + crypto_liquidity + crypto_freshness) / 3.0)
    base_score = (
        0.40 * clamp_unit(agreement_score)
        + 0.25 * clamp_unit(comparison_confidence)
        + 0.20 * market_quality
        + 0.15 * crypto_quality
    )

    penalty = 0.30 * clamp_unit(divergence_score)
    if alignment == "conflicted":
        penalty += 0.24
    elif alignment == "insufficient":
        penalty += 0.20
    elif alignment == "weakly_aligned":
        penalty += 0.07

    if has_stale_flags(flags=flags):
        penalty += 0.08
    if has_missing_probability_flags(flags=flags):
        penalty += 0.10
    if crypto_coverage < 0.55:
        penalty += 0.07
    if min(evidence_liquidity, crypto_liquidity) < 0.40:
        penalty += 0.06

    return round(clamp_unit(base_score - penalty), 3)


def compute_candidate_confidence_score(
    *,
    link_confidence: float,
    comparison_confidence: float,
    evidence_freshness: float,
    evidence_liquidity: float,
    crypto_freshness: float,
    crypto_coverage: float,
    divergence_score: float,
    alignment: str,
    flags: Sequence[str],
) -> float:
    """Compute bounded confidence from link quality, comparison quality, and data sufficiency."""

    evidence_quality = clamp_unit((evidence_freshness + evidence_liquidity) / 2.0)
    crypto_quality = clamp_unit((crypto_freshness + crypto_coverage) / 2.0)
    base_confidence = (
        0.25 * clamp_unit(link_confidence)
        + 0.30 * clamp_unit(comparison_confidence)
        + 0.20 * evidence_quality
        + 0.25 * crypto_quality
    )

    penalty = 0.20 * clamp_unit(divergence_score)
    if alignment == "conflicted":
        penalty += 0.22
    elif alignment == "insufficient":
        penalty += 0.18

    if has_stale_flags(flags=flags):
        penalty += 0.10
    if has_missing_probability_flags(flags=flags):
        penalty += 0.12
    if crypto_coverage < 0.50:
        penalty += 0.08

    return round(clamp_unit(base_confidence - penalty), 3)


def compute_candidate_conflict_score(
    *,
    divergence_score: float,
    alignment: str,
    flags: Sequence[str],
) -> float:
    """Compute bounded candidate conflict from divergence and alignment disagreement."""

    conflict = 0.70 * clamp_unit(divergence_score)

    if alignment == "conflicted":
        conflict += 0.30
    elif alignment == "insufficient":
        conflict += 0.16
    elif alignment == "weakly_aligned":
        conflict += 0.08

    if "high_internal_dispersion" in set(flags):
        conflict += 0.10
    if has_stale_flags(flags=flags):
        conflict += 0.05
    if has_missing_probability_flags(flags=flags):
        conflict += 0.08

    return round(clamp_unit(conflict), 3)


def classify_candidate_posture(
    *,
    candidate_score: float,
    confidence_score: float,
    conflict_score: float,
    alignment: str,
    comparison_confidence: float,
    evidence_score: float,
    crypto_coverage: float,
    has_probability_inputs: bool,
    divergence_score: float,
) -> CandidatePosture:
    """Classify deterministic candidate posture from score thresholds and sufficiency rules."""

    if (
        comparison_confidence < 0.35
        or evidence_score < 0.35
        or crypto_coverage < 0.35
        or not has_probability_inputs
    ):
        return "insufficient"
    if alignment == "insufficient" and comparison_confidence < 0.50:
        return "insufficient"

    if conflict_score >= 0.68 or alignment == "conflicted" or divergence_score >= 0.70:
        return "high_conflict"

    if candidate_score >= 0.65 and confidence_score >= 0.55 and conflict_score < 0.45:
        return "candidate"

    return "watch"


def derive_candidate_reason_codes(
    *,
    alignment: str,
    candidate_score: float,
    comparison_confidence: float,
    conflict_score: float,
    divergence_score: float,
    evidence_liquidity: float,
    evidence_freshness: float,
    crypto_coverage: float,
    crypto_freshness: float,
    has_probability_inputs: bool,
    flags: Sequence[str],
) -> list[CandidateReasonCode]:
    """Derive a short deterministic set of primary candidate reason codes."""

    reason_codes: list[CandidateReasonCode] = []
    flag_set = set(flags)

    if alignment == "conflicted":
        _append_reason(reason_codes, "cross_market_conflict")
    elif alignment == "aligned" and candidate_score >= 0.68 and comparison_confidence >= 0.55:
        _append_reason(reason_codes, "strong_cross_market_alignment")
    elif alignment in {"aligned", "weakly_aligned"}:
        _append_reason(reason_codes, "weak_cross_market_alignment")

    if (
        divergence_score >= 0.60
        or conflict_score >= 0.68
        or "high_internal_dispersion" in flag_set
    ):
        _append_reason(reason_codes, "high_internal_divergence")

    if min(evidence_liquidity, 1.0) < 0.45:
        _append_reason(reason_codes, "weak_liquidity")

    if (
        evidence_freshness <= 0.50
        or crypto_freshness <= 0.50
        or has_stale_flags(flags=flags)
    ):
        _append_reason(reason_codes, "stale_evidence")

    if crypto_coverage < 0.60:
        _append_reason(reason_codes, "weak_crypto_coverage")

    if not has_probability_inputs or has_missing_probability_flags(flags=flags):
        _append_reason(reason_codes, "missing_probability_inputs")

    if comparison_confidence < 0.45 or alignment == "insufficient":
        _append_reason(reason_codes, "insufficient_comparison_confidence")

    return reason_codes


def has_stale_flags(*, flags: Sequence[str]) -> bool:
    """Return whether flags include stale evidence markers."""

    return any(flag in _STALE_FLAGS for flag in flags)


def has_missing_probability_flags(*, flags: Sequence[str]) -> bool:
    """Return whether flags include missing probability markers."""

    return any(flag in _MISSING_PROBABILITY_FLAGS for flag in flags)


def _append_reason(
    reason_codes: list[CandidateReasonCode],
    reason: CandidateReasonCode,
    *,
    max_reasons: int = 5,
) -> None:
    if len(reason_codes) >= max_reasons:
        return
    if reason in reason_codes:
        return
    reason_codes.append(reason)


def clamp_unit(value: float) -> float:
    """Clamp numeric values into the closed unit interval."""

    return max(0.0, min(1.0, value))
