"""Deterministic bounded scoring helpers for theme divergence detection."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.divergence.models import DivergencePosture, MarketDisagreementSeverity

_QUALITY_RELEVANT_FLAGS = frozenset(
    {
        "stale_snapshot",
        "stale_evidence",
        "missing_book_data",
        "missing_implied_probability",
        "missing_probability_inputs",
        "no_aggregate_probability",
        "weak_liquidity",
    }
)


def compute_dispersion_score(*, distances_from_aggregate: Sequence[float]) -> float:
    """Compute bounded internal disagreement from absolute probability distances."""

    if not distances_from_aggregate:
        return 0.0
    bounded_distances = [clamp_unit(max(0.0, distance)) for distance in distances_from_aggregate]
    mean_distance = sum(bounded_distances) / len(bounded_distances)
    return round(clamp_unit(mean_distance / 0.30), 3)


def compute_quality_penalty(
    *,
    liquidity_score: float,
    freshness_score: float,
    flags: Sequence[str],
) -> float:
    """Compute bounded quality weakness from packet-level evidence quality signals."""

    liquidity_weakness = 1.0 - clamp_unit(liquidity_score)
    freshness_weakness = 1.0 - clamp_unit(freshness_score)
    relevant_flags = {flag for flag in flags if flag in _QUALITY_RELEVANT_FLAGS}
    flag_penalty = min(0.4, 0.08 * len(relevant_flags))

    penalty = (0.50 * liquidity_weakness) + (0.35 * freshness_weakness) + flag_penalty
    return round(clamp_unit(penalty), 3)


def compute_divergence_score(*, dispersion_score: float, quality_penalty: float) -> float:
    """Combine disagreement and quality weakness into one bounded divergence score."""

    bounded_dispersion = clamp_unit(dispersion_score)
    bounded_quality = clamp_unit(quality_penalty)
    return round(clamp_unit((0.70 * bounded_dispersion) + (0.30 * bounded_quality)), 3)


def classify_divergence_posture(
    *,
    aggregate_yes_probability: float | None,
    usable_market_count: int,
    total_market_count: int,
    missing_probability_count: int,
    dispersion_score: float,
    quality_penalty: float,
    divergence_score: float,
) -> DivergencePosture:
    """Classify deterministic divergence posture from bounded score and data sufficiency inputs."""

    if aggregate_yes_probability is None:
        return "insufficient"
    if usable_market_count < 2:
        return "insufficient"
    if missing_probability_count > (total_market_count / 2):
        return "insufficient"

    if dispersion_score >= 0.65:
        return "conflicted"
    if dispersion_score >= 0.30 or quality_penalty >= 0.45 or divergence_score >= 0.40:
        return "mixed"
    return "aligned"


def classify_market_disagreement_severity(
    *,
    distance_from_aggregate: float | None,
) -> MarketDisagreementSeverity:
    """Classify one market contribution severity from aggregate-distance buckets."""

    if distance_from_aggregate is None:
        return "unknown"
    distance = clamp_unit(max(0.0, distance_from_aggregate))
    if distance < 0.05:
        return "low"
    if distance < 0.15:
        return "medium"
    return "high"


def clamp_unit(value: float) -> float:
    """Clamp any numeric input into the unit interval."""

    return max(0.0, min(1.0, value))

