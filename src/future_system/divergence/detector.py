"""Deterministic disagreement detector over canonical theme evidence packets."""

from __future__ import annotations

from future_system.divergence.models import (
    DivergenceDetectionError,
    MarketDisagreement,
    ThemeDivergencePacket,
)
from future_system.divergence.scoring import (
    classify_divergence_posture,
    classify_market_disagreement_severity,
    compute_dispersion_score,
    compute_divergence_score,
    compute_quality_penalty,
)
from future_system.evidence.models import ThemeEvidencePacket


def detect_theme_divergence(*, evidence_packet: ThemeEvidencePacket) -> ThemeDivergencePacket:
    """Detect deterministic divergence posture from one canonical evidence packet."""

    if not evidence_packet.market_evidence:
        raise DivergenceDetectionError(
            f"ThemeEvidencePacket for theme {evidence_packet.theme_id!r} has no market_evidence."
        )

    aggregate_probability = evidence_packet.aggregate_yes_probability
    total_markets = len(evidence_packet.market_evidence)
    usable_markets = 0
    missing_probability_count = 0
    distances: list[float] = []
    market_disagreements: list[MarketDisagreement] = []

    for market in evidence_packet.market_evidence:
        distance_from_aggregate: float | None = None
        if market.implied_yes_probability is not None:
            usable_markets += 1
            if aggregate_probability is not None:
                distance_from_aggregate = round(
                    abs(market.implied_yes_probability - aggregate_probability),
                    6,
                )
                distances.append(distance_from_aggregate)
        else:
            missing_probability_count += 1

        market_disagreements.append(
            MarketDisagreement(
                market_slug=market.market_slug,
                condition_id=market.condition_id,
                implied_yes_probability=market.implied_yes_probability,
                distance_from_aggregate=distance_from_aggregate,
                liquidity_score=market.liquidity_score,
                freshness_score=market.freshness_score,
                flags=list(market.flags),
                severity=classify_market_disagreement_severity(
                    distance_from_aggregate=distance_from_aggregate
                ),
            )
        )

    flags = _derive_packet_flags(
        evidence_packet=evidence_packet,
        usable_markets=usable_markets,
        missing_probability_count=missing_probability_count,
    )
    dispersion_score = compute_dispersion_score(distances_from_aggregate=distances)
    if dispersion_score >= 0.60:
        flags.add("high_internal_dispersion")

    quality_penalty = compute_quality_penalty(
        liquidity_score=evidence_packet.liquidity_score,
        freshness_score=evidence_packet.freshness_score,
        flags=sorted(flags),
    )
    divergence_score = compute_divergence_score(
        dispersion_score=dispersion_score,
        quality_penalty=quality_penalty,
    )
    posture = classify_divergence_posture(
        aggregate_yes_probability=aggregate_probability,
        usable_market_count=usable_markets,
        total_market_count=total_markets,
        missing_probability_count=missing_probability_count,
        dispersion_score=dispersion_score,
        quality_penalty=quality_penalty,
        divergence_score=divergence_score,
    )

    aggregate_text = "none" if aggregate_probability is None else f"{aggregate_probability:.3f}"
    flag_list = sorted(flags)
    flag_text = "none" if not flag_list else ",".join(flag_list)
    explanation = (
        f"aggregate_yes_probability={aggregate_text}; "
        f"usable_markets={usable_markets}/{total_markets}; "
        f"posture={posture}; "
        f"flags={flag_text}."
    )

    return ThemeDivergencePacket(
        theme_id=evidence_packet.theme_id,
        primary_market_slug=evidence_packet.primary_market_slug,
        aggregate_yes_probability=aggregate_probability,
        dispersion_score=dispersion_score,
        quality_penalty=quality_penalty,
        divergence_score=divergence_score,
        posture=posture,
        market_disagreements=market_disagreements,
        flags=flag_list,
        explanation=explanation,
    )


def _derive_packet_flags(
    *,
    evidence_packet: ThemeEvidencePacket,
    usable_markets: int,
    missing_probability_count: int,
) -> set[str]:
    flags = set(evidence_packet.flags)
    market_flags = {flag for market in evidence_packet.market_evidence for flag in market.flags}
    flags.update(market_flags)

    if evidence_packet.aggregate_yes_probability is None:
        flags.add("no_aggregate_probability")
    if missing_probability_count > 0:
        flags.add("missing_probability_inputs")
    if usable_markets == 1:
        flags.add("single_usable_market")
    if evidence_packet.liquidity_score < 0.45:
        flags.add("weak_liquidity")
    if evidence_packet.freshness_score <= 0.50 or "stale_snapshot" in flags:
        flags.add("stale_evidence")

    return flags

