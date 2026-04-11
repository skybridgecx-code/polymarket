"""Deterministic builder turning upstream theme packets into candidate signal packets."""

from __future__ import annotations

from future_system.candidates.models import (
    CandidateBuildError,
    CandidateReasonCode,
    CandidateSignalPacket,
)
from future_system.candidates.scoring import (
    classify_candidate_posture,
    compute_candidate_confidence_score,
    compute_candidate_conflict_score,
    compute_candidate_score,
    derive_candidate_reason_codes,
)
from future_system.comparison.models import ThemeComparisonPacket
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.theme_graph.models import ThemeLinkPacket

_IMPORTANT_UPSTREAM_FLAGS = frozenset(
    {
        "cross_market_conflict",
        "crypto_unknown_direction",
        "high_internal_dispersion",
        "missing_implied_probability",
        "missing_probability_inputs",
        "no_aggregate_probability",
        "polymarket_unknown_direction",
        "stale_crypto_evidence",
        "stale_evidence",
        "stale_polymarket_evidence",
        "stale_snapshot",
        "weak_crypto_coverage",
        "weak_liquidity",
    }
)


def build_candidate_signal_packet(
    *,
    link_packet: ThemeLinkPacket,
    evidence_packet: ThemeEvidencePacket,
    divergence_packet: ThemeDivergencePacket,
    crypto_packet: ThemeCryptoEvidencePacket,
    comparison_packet: ThemeComparisonPacket,
) -> CandidateSignalPacket:
    """Build one deterministic candidate signal packet from canonical upstream packets."""

    theme_id = _require_matching_theme_id(
        link_packet=link_packet,
        evidence_packet=evidence_packet,
        divergence_packet=divergence_packet,
        crypto_packet=crypto_packet,
        comparison_packet=comparison_packet,
    )

    flags = _derive_candidate_flags(
        link_packet=link_packet,
        evidence_packet=evidence_packet,
        divergence_packet=divergence_packet,
        crypto_packet=crypto_packet,
        comparison_packet=comparison_packet,
    )
    has_probability_inputs = (
        evidence_packet.aggregate_yes_probability is not None
        and "missing_probability_inputs" not in flags
        and "no_aggregate_probability" not in flags
    )

    alignment = str(comparison_packet.alignment)
    candidate_score = compute_candidate_score(
        agreement_score=comparison_packet.agreement_score,
        comparison_confidence=comparison_packet.confidence_score,
        evidence_score=evidence_packet.evidence_score,
        evidence_liquidity=evidence_packet.liquidity_score,
        evidence_freshness=evidence_packet.freshness_score,
        crypto_coverage=crypto_packet.coverage_score,
        crypto_liquidity=crypto_packet.liquidity_score,
        crypto_freshness=crypto_packet.freshness_score,
        divergence_score=divergence_packet.divergence_score,
        alignment=alignment,
        flags=flags,
    )
    confidence_score = compute_candidate_confidence_score(
        link_confidence=link_packet.confidence_score,
        comparison_confidence=comparison_packet.confidence_score,
        evidence_freshness=evidence_packet.freshness_score,
        evidence_liquidity=evidence_packet.liquidity_score,
        crypto_freshness=crypto_packet.freshness_score,
        crypto_coverage=crypto_packet.coverage_score,
        divergence_score=divergence_packet.divergence_score,
        alignment=alignment,
        flags=flags,
    )
    conflict_score = compute_candidate_conflict_score(
        divergence_score=divergence_packet.divergence_score,
        alignment=alignment,
        flags=flags,
    )

    posture = classify_candidate_posture(
        candidate_score=candidate_score,
        confidence_score=confidence_score,
        conflict_score=conflict_score,
        alignment=alignment,
        comparison_confidence=comparison_packet.confidence_score,
        evidence_score=evidence_packet.evidence_score,
        crypto_coverage=crypto_packet.coverage_score,
        has_probability_inputs=has_probability_inputs,
        divergence_score=divergence_packet.divergence_score,
    )
    reason_codes = derive_candidate_reason_codes(
        alignment=alignment,
        candidate_score=candidate_score,
        comparison_confidence=comparison_packet.confidence_score,
        conflict_score=conflict_score,
        divergence_score=divergence_packet.divergence_score,
        evidence_liquidity=evidence_packet.liquidity_score,
        evidence_freshness=evidence_packet.freshness_score,
        crypto_coverage=crypto_packet.coverage_score,
        crypto_freshness=crypto_packet.freshness_score,
        has_probability_inputs=has_probability_inputs,
        flags=flags,
    )

    return CandidateSignalPacket(
        theme_id=theme_id,
        title=_resolve_title(link_packet=link_packet),
        posture=posture,
        candidate_score=candidate_score,
        confidence_score=confidence_score,
        conflict_score=conflict_score,
        alignment=alignment,
        primary_market_slug=(
            evidence_packet.primary_market_slug or divergence_packet.primary_market_slug
        ),
        primary_symbol=crypto_packet.primary_symbol,
        reason_codes=reason_codes,
        flags=flags,
        explanation=_build_explanation(
            posture=posture,
            candidate_score=candidate_score,
            confidence_score=confidence_score,
            conflict_score=conflict_score,
            alignment=alignment,
            reason_codes=reason_codes,
        ),
    )


def _require_matching_theme_id(
    *,
    link_packet: ThemeLinkPacket,
    evidence_packet: ThemeEvidencePacket,
    divergence_packet: ThemeDivergencePacket,
    crypto_packet: ThemeCryptoEvidencePacket,
    comparison_packet: ThemeComparisonPacket,
) -> str:
    theme_ids = {
        "link": link_packet.theme_id,
        "evidence": evidence_packet.theme_id,
        "divergence": divergence_packet.theme_id,
        "crypto": crypto_packet.theme_id,
        "comparison": comparison_packet.theme_id,
    }
    if len(set(theme_ids.values())) != 1:
        ordered = ", ".join(f"{name}={theme_id!r}" for name, theme_id in theme_ids.items())
        raise CandidateBuildError(f"theme_id_mismatch: {ordered}")
    return link_packet.theme_id


def _resolve_title(*, link_packet: ThemeLinkPacket) -> str | None:
    candidate_title = getattr(link_packet, "title", None)
    if not isinstance(candidate_title, str):
        return None
    normalized = candidate_title.strip()
    return normalized or None


def _derive_candidate_flags(
    *,
    link_packet: ThemeLinkPacket,
    evidence_packet: ThemeEvidencePacket,
    divergence_packet: ThemeDivergencePacket,
    crypto_packet: ThemeCryptoEvidencePacket,
    comparison_packet: ThemeComparisonPacket,
) -> list[str]:
    flags: set[str] = set(link_packet.ambiguity_flags)

    for source_flags in (
        evidence_packet.flags,
        divergence_packet.flags,
        crypto_packet.flags,
        comparison_packet.flags,
    ):
        for flag in source_flags:
            if flag in _IMPORTANT_UPSTREAM_FLAGS:
                flags.add(flag)

    if comparison_packet.alignment == "conflicted":
        flags.add("cross_market_conflict")
    if divergence_packet.divergence_score >= 0.60:
        flags.add("high_internal_divergence")
    if evidence_packet.aggregate_yes_probability is None:
        flags.add("missing_probability_inputs")
    if crypto_packet.coverage_score < 0.60:
        flags.add("weak_crypto_coverage")
    if (
        comparison_packet.alignment == "insufficient"
        and comparison_packet.confidence_score < 0.45
    ):
        flags.add("insufficient_comparison_confidence")

    return sorted(flags)


def _build_explanation(
    *,
    posture: str,
    candidate_score: float,
    confidence_score: float,
    conflict_score: float,
    alignment: str,
    reason_codes: list[CandidateReasonCode],
) -> str:
    reasons_text = "none" if not reason_codes else ",".join(reason_codes)
    return (
        f"posture={posture}; "
        f"candidate_score={candidate_score:.3f}; "
        f"confidence_score={confidence_score:.3f}; "
        f"conflict_score={conflict_score:.3f}; "
        f"alignment={alignment}; "
        f"reasons={reasons_text}."
    )
