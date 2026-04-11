"""Deterministic bounded scoring helpers for evidence assembly."""

from __future__ import annotations

from collections.abc import Sequence


def compute_liquidity_score(
    *,
    spread: float | None,
    depth_near_mid: float | None,
    volume_24h: float | None,
) -> float:
    """Compute a bounded liquidity score from spread, depth, and volume."""

    spread_component = 0.4 if spread is None else clamp_unit(1.0 - spread)
    depth_component = clamp_unit((depth_near_mid or 0.0) / 5_000.0)
    volume_component = clamp_unit((volume_24h or 0.0) / 100_000.0)

    raw_score = (0.50 * spread_component) + (0.30 * depth_component) + (0.20 * volume_component)
    return round(clamp_unit(raw_score), 3)


def compute_evidence_score(*, liquidity_score: float, freshness_score: float) -> float:
    """Combine packet liquidity and freshness into one bounded evidence score."""

    bounded_liquidity = clamp_unit(liquidity_score)
    bounded_freshness = clamp_unit(freshness_score)
    return round(clamp_unit((0.60 * bounded_liquidity) + (0.40 * bounded_freshness)), 3)


def weighted_probability_average(
    *,
    probabilities: Sequence[float],
    weights: Sequence[float],
) -> float | None:
    """Compute a weighted average probability using non-negative weight inputs."""

    if not probabilities:
        return None
    if len(probabilities) != len(weights):
        raise ValueError("probabilities and weights must have identical lengths.")

    bounded_probabilities = [clamp_unit(probability) for probability in probabilities]
    bounded_weights = [max(weight, 0.0) for weight in weights]
    total_weight = sum(bounded_weights)

    if total_weight <= 0.0:
        return round(sum(bounded_probabilities) / len(bounded_probabilities), 6)

    weighted = sum(
        probability * weight
        for probability, weight in zip(bounded_probabilities, bounded_weights, strict=True)
    )
    return round(clamp_unit(weighted / total_weight), 6)


def clamp_unit(value: float) -> float:
    """Clamp any numeric score into the closed unit interval."""

    return max(0.0, min(1.0, value))
