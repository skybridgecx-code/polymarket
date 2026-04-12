"""Deterministic builder for canonical opportunity context bundles."""

from __future__ import annotations

from typing import Any

from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.models import (
    BundleComponentStatus,
    BundleQualitySummary,
    ContextBundleError,
    OpportunityContextBundle,
)
from future_system.context_bundle.summary import build_operator_summary
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.theme_graph.models import ThemeLinkPacket

_COMPONENT_KEYS = (
    "theme_link",
    "polymarket_evidence",
    "divergence",
    "crypto_evidence",
    "comparison",
    "news_evidence",
    "candidate",
)


def build_opportunity_context_bundle(
    *,
    theme_link_packet: ThemeLinkPacket,
    polymarket_evidence_packet: ThemeEvidencePacket,
    divergence_packet: ThemeDivergencePacket,
    crypto_evidence_packet: ThemeCryptoEvidencePacket,
    comparison_packet: ThemeComparisonPacket,
    news_evidence_packet: ThemeNewsEvidencePacket,
    candidate_packet: CandidateSignalPacket,
) -> OpportunityContextBundle:
    """Build one deterministic context bundle from all canonical upstream packets."""

    theme_id = _require_matching_theme_id(
        theme_link_packet=theme_link_packet,
        polymarket_evidence_packet=polymarket_evidence_packet,
        divergence_packet=divergence_packet,
        crypto_evidence_packet=crypto_evidence_packet,
        comparison_packet=comparison_packet,
        news_evidence_packet=news_evidence_packet,
        candidate_packet=candidate_packet,
    )

    component_statuses = _derive_component_statuses(
        theme_link_packet=theme_link_packet,
        polymarket_evidence_packet=polymarket_evidence_packet,
        divergence_packet=divergence_packet,
        crypto_evidence_packet=crypto_evidence_packet,
        comparison_packet=comparison_packet,
        news_evidence_packet=news_evidence_packet,
        candidate_packet=candidate_packet,
    )

    completeness_score = _compute_completeness_score(component_statuses=component_statuses)
    freshness_score = _compute_freshness_score(
        polymarket_evidence_packet=polymarket_evidence_packet,
        crypto_evidence_packet=crypto_evidence_packet,
        news_evidence_packet=news_evidence_packet,
    )
    confidence_score = _compute_confidence_score(
        candidate_packet=candidate_packet,
        comparison_packet=comparison_packet,
        polymarket_evidence_packet=polymarket_evidence_packet,
        crypto_evidence_packet=crypto_evidence_packet,
        news_evidence_packet=news_evidence_packet,
    )
    conflict_score = _compute_conflict_score(
        divergence_packet=divergence_packet,
        comparison_packet=comparison_packet,
        candidate_packet=candidate_packet,
    )

    bundle_flags = _derive_bundle_flags(
        component_statuses=component_statuses,
        completeness_score=completeness_score,
        freshness_score=freshness_score,
        crypto_evidence_packet=crypto_evidence_packet,
        news_evidence_packet=news_evidence_packet,
        divergence_packet=divergence_packet,
        comparison_packet=comparison_packet,
        candidate_packet=candidate_packet,
    )

    quality_summary = BundleQualitySummary(
        completeness_score=completeness_score,
        freshness_score=freshness_score,
        confidence_score=confidence_score,
        conflict_score=conflict_score,
        component_statuses=component_statuses,
        flags=bundle_flags,
    )

    operator_summary = build_operator_summary(
        theme_id=theme_id,
        candidate_posture=candidate_packet.posture,
        comparison_alignment=comparison_packet.alignment,
        completeness_score=completeness_score,
        freshness_score=freshness_score,
        confidence_score=confidence_score,
        conflict_score=conflict_score,
        flags=bundle_flags,
    )

    return OpportunityContextBundle(
        theme_id=theme_id,
        title=_resolve_title(
            theme_link_packet=theme_link_packet,
            candidate_packet=candidate_packet,
        ),
        theme_link=theme_link_packet,
        polymarket_evidence=polymarket_evidence_packet,
        divergence=divergence_packet,
        crypto_evidence=crypto_evidence_packet,
        comparison=comparison_packet,
        news_evidence=news_evidence_packet,
        candidate=candidate_packet,
        quality=quality_summary,
        operator_summary=operator_summary,
        flags=bundle_flags,
    )


def export_opportunity_context_bundle(bundle: OpportunityContextBundle) -> dict[str, Any]:
    """Return a stable JSON-ready export shape for one context bundle."""

    return {
        "theme_id": bundle.theme_id,
        "title": bundle.title,
        "theme_link": bundle.theme_link.model_dump(mode="json"),
        "polymarket_evidence": bundle.polymarket_evidence.model_dump(mode="json"),
        "divergence": bundle.divergence.model_dump(mode="json"),
        "crypto_evidence": bundle.crypto_evidence.model_dump(mode="json"),
        "comparison": bundle.comparison.model_dump(mode="json"),
        "news_evidence": bundle.news_evidence.model_dump(mode="json"),
        "candidate": bundle.candidate.model_dump(mode="json"),
        "quality": {
            "completeness_score": bundle.quality.completeness_score,
            "freshness_score": bundle.quality.freshness_score,
            "confidence_score": bundle.quality.confidence_score,
            "conflict_score": bundle.quality.conflict_score,
            "component_statuses": dict(bundle.quality.component_statuses),
            "flags": list(bundle.quality.flags),
        },
        "operator_summary": bundle.operator_summary,
        "flags": list(bundle.flags),
    }


def _require_matching_theme_id(
    *,
    theme_link_packet: ThemeLinkPacket,
    polymarket_evidence_packet: ThemeEvidencePacket,
    divergence_packet: ThemeDivergencePacket,
    crypto_evidence_packet: ThemeCryptoEvidencePacket,
    comparison_packet: ThemeComparisonPacket,
    news_evidence_packet: ThemeNewsEvidencePacket,
    candidate_packet: CandidateSignalPacket,
) -> str:
    theme_ids = {
        "theme_link": theme_link_packet.theme_id,
        "polymarket_evidence": polymarket_evidence_packet.theme_id,
        "divergence": divergence_packet.theme_id,
        "crypto_evidence": crypto_evidence_packet.theme_id,
        "comparison": comparison_packet.theme_id,
        "news_evidence": news_evidence_packet.theme_id,
        "candidate": candidate_packet.theme_id,
    }
    if len(set(theme_ids.values())) != 1:
        ordered = ", ".join(f"{name}={theme_id!r}" for name, theme_id in theme_ids.items())
        raise ContextBundleError(f"theme_id_mismatch: {ordered}")
    return theme_link_packet.theme_id


def _resolve_title(
    *,
    theme_link_packet: ThemeLinkPacket,
    candidate_packet: CandidateSignalPacket,
) -> str | None:
    if candidate_packet.title is not None:
        return candidate_packet.title

    link_title = getattr(theme_link_packet, "title", None)
    if isinstance(link_title, str):
        normalized = link_title.strip()
        if normalized:
            return normalized
    return None


def _derive_component_statuses(
    *,
    theme_link_packet: ThemeLinkPacket,
    polymarket_evidence_packet: ThemeEvidencePacket,
    divergence_packet: ThemeDivergencePacket,
    crypto_evidence_packet: ThemeCryptoEvidencePacket,
    comparison_packet: ThemeComparisonPacket,
    news_evidence_packet: ThemeNewsEvidencePacket,
    candidate_packet: CandidateSignalPacket,
) -> dict[str, BundleComponentStatus]:
    return {
        "theme_link": _theme_link_status(theme_link_packet),
        "polymarket_evidence": _polymarket_status(polymarket_evidence_packet),
        "divergence": _divergence_status(divergence_packet),
        "crypto_evidence": _crypto_status(crypto_evidence_packet),
        "comparison": _comparison_status(comparison_packet),
        "news_evidence": _news_status(news_evidence_packet),
        "candidate": _candidate_status(candidate_packet),
    }


def _theme_link_status(packet: ThemeLinkPacket) -> BundleComponentStatus:
    has_links = bool(
        packet.matched_polymarket_markets or packet.matched_assets or packet.matched_entities
    )
    if not has_links:
        return "missing"
    if packet.confidence_score < 0.45:
        return "partial"
    return "present"


def _polymarket_status(packet: ThemeEvidencePacket) -> BundleComponentStatus:
    if not packet.market_evidence:
        return "missing"
    if (
        packet.aggregate_yes_probability is None
        or packet.evidence_score < 0.45
        or "missing_probability_inputs" in set(packet.flags)
    ):
        return "partial"
    return "present"


def _divergence_status(packet: ThemeDivergencePacket) -> BundleComponentStatus:
    if not packet.market_disagreements:
        return "missing"
    if packet.posture == "insufficient":
        return "partial"
    return "present"


def _crypto_status(packet: ThemeCryptoEvidencePacket) -> BundleComponentStatus:
    if not packet.proxy_evidence:
        return "missing"
    if packet.coverage_score < 0.50 or packet.freshness_score < 0.50:
        return "partial"
    return "present"


def _comparison_status(packet: ThemeComparisonPacket) -> BundleComponentStatus:
    if packet.confidence_score < 0.20:
        return "missing"
    if packet.alignment == "insufficient" or packet.confidence_score < 0.50:
        return "partial"
    return "present"


def _news_status(packet: ThemeNewsEvidencePacket) -> BundleComponentStatus:
    if not packet.matched_records or packet.matched_article_count <= 0:
        return "missing"
    if packet.coverage_score < 0.50 or packet.freshness_score < 0.35 or packet.trust_score < 0.55:
        return "partial"
    return "present"


def _candidate_status(packet: CandidateSignalPacket) -> BundleComponentStatus:
    if packet.posture == "insufficient":
        return "partial"
    return "present"


def _compute_completeness_score(
    *,
    component_statuses: dict[str, BundleComponentStatus],
) -> float:
    status_values = {"present": 1.0, "partial": 0.5, "missing": 0.0}
    total = sum(status_values[component_statuses[key]] for key in _COMPONENT_KEYS)
    return round(clamp_unit(total / len(_COMPONENT_KEYS)), 3)


def _compute_freshness_score(
    *,
    polymarket_evidence_packet: ThemeEvidencePacket,
    crypto_evidence_packet: ThemeCryptoEvidencePacket,
    news_evidence_packet: ThemeNewsEvidencePacket,
) -> float:
    raw = (
        polymarket_evidence_packet.freshness_score
        + crypto_evidence_packet.freshness_score
        + news_evidence_packet.freshness_score
    ) / 3.0
    return round(clamp_unit(raw), 3)


def _compute_confidence_score(
    *,
    candidate_packet: CandidateSignalPacket,
    comparison_packet: ThemeComparisonPacket,
    polymarket_evidence_packet: ThemeEvidencePacket,
    crypto_evidence_packet: ThemeCryptoEvidencePacket,
    news_evidence_packet: ThemeNewsEvidencePacket,
) -> float:
    raw = (
        0.35 * candidate_packet.confidence_score
        + 0.25 * comparison_packet.confidence_score
        + 0.15 * polymarket_evidence_packet.evidence_score
        + 0.15 * crypto_evidence_packet.coverage_score
        + 0.10 * news_evidence_packet.trust_score
    )
    return round(clamp_unit(raw), 3)


def _compute_conflict_score(
    *,
    divergence_packet: ThemeDivergencePacket,
    comparison_packet: ThemeComparisonPacket,
    candidate_packet: CandidateSignalPacket,
) -> float:
    alignment_conflict = {
        "aligned": 0.05,
        "weakly_aligned": 0.25,
        "conflicted": 1.0,
        "insufficient": 0.50,
    }[comparison_packet.alignment]

    raw = (
        0.55 * divergence_packet.divergence_score
        + 0.30 * alignment_conflict
        + 0.15 * candidate_packet.conflict_score
    )

    if comparison_packet.alignment == "conflicted" or "cross_market_conflict" in set(
        comparison_packet.flags
    ):
        raw += 0.10
    if divergence_packet.divergence_score >= 0.65 or "high_internal_dispersion" in set(
        divergence_packet.flags
    ):
        raw += 0.08

    return round(clamp_unit(raw), 3)


def _derive_bundle_flags(
    *,
    component_statuses: dict[str, BundleComponentStatus],
    completeness_score: float,
    freshness_score: float,
    crypto_evidence_packet: ThemeCryptoEvidencePacket,
    news_evidence_packet: ThemeNewsEvidencePacket,
    divergence_packet: ThemeDivergencePacket,
    comparison_packet: ThemeComparisonPacket,
    candidate_packet: CandidateSignalPacket,
) -> list[str]:
    flags: set[str] = set()

    if (
        completeness_score < 0.75
        or any(status == "missing" for status in component_statuses.values())
    ):
        flags.add("context_incomplete")

    stale_markers = {
        "stale_snapshot",
        "stale_evidence",
        "stale_news_evidence",
        "stale_crypto_evidence",
        "stale_polymarket_evidence",
    }
    upstream_flags = set(
        crypto_evidence_packet.flags
        + news_evidence_packet.flags
        + comparison_packet.flags
        + divergence_packet.flags
        + candidate_packet.flags
    )
    if freshness_score < 0.50 or any(marker in upstream_flags for marker in stale_markers):
        flags.add("stale_context")

    if (
        component_statuses["news_evidence"] != "present"
        or news_evidence_packet.coverage_score < 0.60
        or news_evidence_packet.trust_score < 0.60
    ):
        flags.add("weak_news_context")

    if (
        component_statuses["crypto_evidence"] != "present"
        or crypto_evidence_packet.coverage_score < 0.60
    ):
        flags.add("weak_crypto_context")

    if comparison_packet.alignment == "conflicted" or "cross_market_conflict" in upstream_flags:
        flags.add("cross_market_conflict")

    if (
        divergence_packet.divergence_score >= 0.65
        or divergence_packet.posture == "conflicted"
        or "high_internal_divergence" in upstream_flags
        or "high_internal_dispersion" in upstream_flags
    ):
        flags.add("high_internal_divergence")

    if candidate_packet.posture == "insufficient":
        flags.add("candidate_insufficient")

    return sorted(flags)


def clamp_unit(value: float) -> float:
    """Clamp numeric values into the closed unit interval."""

    return max(0.0, min(1.0, value))
