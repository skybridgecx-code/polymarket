"""Deterministic comparator between canonical Polymarket and crypto evidence packets."""

from __future__ import annotations

from future_system.comparison.models import (
    ComparisonError,
    EvidenceFamilySummary,
    ThemeComparisonPacket,
)
from future_system.comparison.scoring import (
    classify_alignment,
    compute_agreement_score,
    compute_comparison_confidence_score,
    compute_crypto_strength_score,
    compute_polymarket_strength_score,
    derive_crypto_direction,
    derive_polymarket_direction,
)
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.evidence.models import ThemeEvidencePacket


def compare_theme_evidence_packets(
    *,
    polymarket_packet: ThemeEvidencePacket,
    crypto_packet: ThemeCryptoEvidencePacket,
) -> ThemeComparisonPacket:
    """Compare two canonical evidence families for one theme, deterministically."""

    if polymarket_packet.theme_id != crypto_packet.theme_id:
        raise ComparisonError(
            "theme_id_mismatch: "
            f"{polymarket_packet.theme_id!r} != {crypto_packet.theme_id!r}"
        )

    polymarket_direction = derive_polymarket_direction(
        aggregate_yes_probability=polymarket_packet.aggregate_yes_probability
    )
    crypto_direction = derive_crypto_direction(proxy_evidence=crypto_packet.proxy_evidence)

    polymarket_strength = compute_polymarket_strength_score(
        evidence_score=polymarket_packet.evidence_score,
        liquidity_score=polymarket_packet.liquidity_score,
        freshness_score=polymarket_packet.freshness_score,
        has_aggregate_probability=polymarket_packet.aggregate_yes_probability is not None,
        flags=polymarket_packet.flags,
    )
    crypto_strength = compute_crypto_strength_score(
        liquidity_score=crypto_packet.liquidity_score,
        freshness_score=crypto_packet.freshness_score,
        coverage_score=crypto_packet.coverage_score,
        flags=crypto_packet.flags,
    )

    agreement_score = compute_agreement_score(
        polymarket_direction=polymarket_direction,
        crypto_direction=crypto_direction,
        polymarket_strength=polymarket_strength,
        crypto_strength=crypto_strength,
    )

    flags = _derive_comparison_flags(
        polymarket_packet=polymarket_packet,
        crypto_packet=crypto_packet,
        polymarket_direction=polymarket_direction,
        crypto_direction=crypto_direction,
    )
    confidence_score = compute_comparison_confidence_score(
        agreement_score=agreement_score,
        polymarket_strength=polymarket_strength,
        crypto_strength=crypto_strength,
        flags=sorted(flags),
    )
    alignment = classify_alignment(
        polymarket_direction=polymarket_direction,
        crypto_direction=crypto_direction,
        agreement_score=agreement_score,
        confidence_score=confidence_score,
        polymarket_strength=polymarket_strength,
        crypto_strength=crypto_strength,
    )
    if alignment == "conflicted":
        flags.add("cross_market_conflict")

    sorted_flags = sorted(flags)
    flag_text = "none" if not sorted_flags else ",".join(sorted_flags)
    explanation = (
        f"polymarket_direction={polymarket_direction}; "
        f"crypto_direction={crypto_direction}; "
        f"alignment={alignment}; "
        f"agreement_score={agreement_score:.3f}; "
        f"confidence_score={confidence_score:.3f}; "
        f"flags={flag_text}."
    )

    polymarket_summary = EvidenceFamilySummary(
        family="polymarket",
        direction=polymarket_direction,
        strength_score=polymarket_strength,
        freshness_score=polymarket_packet.freshness_score,
        liquidity_score=polymarket_packet.liquidity_score,
        coverage_score=None,
        flags=sorted(set(polymarket_packet.flags)),
    )
    crypto_summary = EvidenceFamilySummary(
        family="crypto",
        direction=crypto_direction,
        strength_score=crypto_strength,
        freshness_score=crypto_packet.freshness_score,
        liquidity_score=crypto_packet.liquidity_score,
        coverage_score=crypto_packet.coverage_score,
        flags=sorted(set(crypto_packet.flags)),
    )

    return ThemeComparisonPacket(
        theme_id=polymarket_packet.theme_id,
        polymarket_summary=polymarket_summary,
        crypto_summary=crypto_summary,
        alignment=alignment,
        agreement_score=agreement_score,
        confidence_score=confidence_score,
        flags=sorted_flags,
        explanation=explanation,
    )


def _derive_comparison_flags(
    *,
    polymarket_packet: ThemeEvidencePacket,
    crypto_packet: ThemeCryptoEvidencePacket,
    polymarket_direction: str,
    crypto_direction: str,
) -> set[str]:
    flags: set[str] = set()

    if polymarket_direction == "unknown":
        flags.add("polymarket_unknown_direction")
    if crypto_direction == "unknown":
        flags.add("crypto_unknown_direction")
    if crypto_packet.coverage_score < 0.60:
        flags.add("weak_crypto_coverage")
    if (
        polymarket_packet.freshness_score <= 0.50
        or "stale_snapshot" in polymarket_packet.flags
        or "stale_evidence" in polymarket_packet.flags
    ):
        flags.add("stale_polymarket_evidence")
    if (
        crypto_packet.freshness_score <= 0.50
        or "stale_snapshot" in crypto_packet.flags
        or "stale_crypto_evidence" in crypto_packet.flags
    ):
        flags.add("stale_crypto_evidence")

    return flags

