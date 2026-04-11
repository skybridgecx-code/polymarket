"""Deterministic scoring helpers for Polymarket-vs-crypto comparison."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.comparison.models import ComparisonAlignment, ComparisonDirection
from future_system.crypto_evidence.models import CryptoProxyEvidence

_ROLE_WEIGHTS = {
    "primary_proxy": 1.0,
    "confirmation_proxy": 0.8,
    "hedge_proxy": 0.6,
    "context_only": 0.35,
}


def derive_polymarket_direction(*, aggregate_yes_probability: float | None) -> ComparisonDirection:
    """Derive deterministic direction from Polymarket aggregate probability."""

    if aggregate_yes_probability is None:
        return "unknown"
    if aggregate_yes_probability > 0.55:
        return "bullish"
    if aggregate_yes_probability < 0.45:
        return "bearish"
    return "mixed"


def derive_crypto_direction(
    *,
    proxy_evidence: Sequence[CryptoProxyEvidence],
) -> ComparisonDirection:
    """Derive deterministic crypto direction from role-weighted usable proxies."""

    bullish_weight = 0.0
    bearish_weight = 0.0
    mixed_weight = 0.0

    for proxy in proxy_evidence:
        if proxy.last_price is None and proxy.mid_price is None:
            continue
        weight = _ROLE_WEIGHTS[proxy.role]
        if proxy.direction_if_theme_up == "up":
            bullish_weight += weight
        elif proxy.direction_if_theme_up == "down":
            bearish_weight += weight
        elif proxy.direction_if_theme_up == "mixed":
            mixed_weight += weight

    usable_weight = bullish_weight + bearish_weight + mixed_weight
    if usable_weight < 0.5:
        return "unknown"
    if bullish_weight == 0.0 and bearish_weight == 0.0 and mixed_weight > 0.0:
        return "mixed"
    if bullish_weight > (bearish_weight * 1.15) and (bullish_weight - bearish_weight) >= 0.15:
        return "bullish"
    if bearish_weight > (bullish_weight * 1.15) and (bearish_weight - bullish_weight) >= 0.15:
        return "bearish"
    return "mixed"


def compute_polymarket_strength_score(
    *,
    evidence_score: float,
    liquidity_score: float,
    freshness_score: float,
    has_aggregate_probability: bool,
    flags: Sequence[str],
) -> float:
    """Compute bounded Polymarket family strength from packet quality signals."""

    score = (
        0.45 * clamp_unit(evidence_score)
        + 0.30 * clamp_unit(liquidity_score)
        + 0.25 * clamp_unit(freshness_score)
    )
    if not has_aggregate_probability:
        score *= 0.60

    penalty = 0.0
    if freshness_score <= 0.50 or "stale_snapshot" in flags or "stale_evidence" in flags:
        penalty += 0.10
    if "missing_implied_probability" in flags or "missing_probability_inputs" in flags:
        penalty += 0.08

    return round(clamp_unit(score - penalty), 3)


def compute_crypto_strength_score(
    *,
    liquidity_score: float,
    freshness_score: float,
    coverage_score: float,
    flags: Sequence[str],
) -> float:
    """Compute bounded crypto family strength from packet quality signals."""

    score = (
        0.40 * clamp_unit(coverage_score)
        + 0.35 * clamp_unit(liquidity_score)
        + 0.25 * clamp_unit(freshness_score)
    )

    penalty = 0.0
    if coverage_score < 0.60:
        penalty += 0.10
    if freshness_score <= 0.50 or "stale_snapshot" in flags or "stale_crypto_evidence" in flags:
        penalty += 0.10
    if "missing_price_data" in flags:
        penalty += 0.08

    return round(clamp_unit(score - penalty), 3)


def compute_agreement_score(
    *,
    polymarket_direction: ComparisonDirection,
    crypto_direction: ComparisonDirection,
    polymarket_strength: float,
    crypto_strength: float,
) -> float:
    """Compute bounded directional agreement score across evidence families."""

    if "unknown" in {polymarket_direction, crypto_direction}:
        return 0.0

    if polymarket_direction == crypto_direction and polymarket_direction in {"bullish", "bearish"}:
        base = 1.0
    elif "mixed" in {polymarket_direction, crypto_direction}:
        base = 0.55
    else:
        base = 0.10

    quality_factor = 0.5 + 0.5 * clamp_unit((polymarket_strength + crypto_strength) / 2.0)
    return round(clamp_unit(base * quality_factor), 3)


def compute_comparison_confidence_score(
    *,
    agreement_score: float,
    polymarket_strength: float,
    crypto_strength: float,
    flags: Sequence[str],
) -> float:
    """Compute bounded confidence from agreement plus evidence-family quality."""

    quality = clamp_unit((polymarket_strength + crypto_strength) / 2.0)
    penalty = 0.0
    if "polymarket_unknown_direction" in flags:
        penalty += 0.25
    if "crypto_unknown_direction" in flags:
        penalty += 0.25
    if "weak_crypto_coverage" in flags:
        penalty += 0.12
    if "stale_polymarket_evidence" in flags:
        penalty += 0.08
    if "stale_crypto_evidence" in flags:
        penalty += 0.08

    raw_confidence = 0.60 * clamp_unit(agreement_score) + 0.40 * quality - penalty
    return round(clamp_unit(raw_confidence), 3)


def classify_alignment(
    *,
    polymarket_direction: ComparisonDirection,
    crypto_direction: ComparisonDirection,
    agreement_score: float,
    confidence_score: float,
    polymarket_strength: float,
    crypto_strength: float,
) -> ComparisonAlignment:
    """Classify deterministic cross-market alignment posture."""

    if "unknown" in {polymarket_direction, crypto_direction}:
        return "insufficient"
    if polymarket_strength < 0.25 or crypto_strength < 0.25:
        return "insufficient"

    if (
        polymarket_direction == "bullish" and crypto_direction == "bearish"
    ) or (
        polymarket_direction == "bearish" and crypto_direction == "bullish"
    ):
        if ((polymarket_strength + crypto_strength) / 2.0) >= 0.35:
            return "conflicted"
        return "insufficient"

    if (
        polymarket_direction == crypto_direction
        and polymarket_direction in {"bullish", "bearish"}
    ):
        if agreement_score >= 0.68 and confidence_score >= 0.55:
            return "aligned"
        return "weakly_aligned"

    if agreement_score >= 0.35 and confidence_score >= 0.30:
        return "weakly_aligned"
    return "insufficient"


def clamp_unit(value: float) -> float:
    """Clamp numeric scores into the closed unit interval."""

    return max(0.0, min(1.0, value))
