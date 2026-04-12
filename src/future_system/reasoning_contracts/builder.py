"""Deterministic builder for reasoning input packets from opportunity context bundles."""

from __future__ import annotations

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.reasoning_contracts.models import ReasoningInputPacket

PROMPT_VERSION = "v1"
_MAX_BUNDLE_FLAGS = 5


def build_reasoning_input_packet(*, bundle: OpportunityContextBundle) -> ReasoningInputPacket:
    """Build canonical reasoning input packet from one opportunity context bundle."""

    structured_facts = _build_structured_facts(bundle=bundle)
    return ReasoningInputPacket(
        theme_id=bundle.theme_id,
        title=bundle.title,
        candidate_posture=bundle.candidate.posture,
        comparison_alignment=bundle.comparison.alignment,
        candidate_score=bundle.candidate.candidate_score,
        confidence_score=bundle.candidate.confidence_score,
        conflict_score=bundle.candidate.conflict_score,
        bundle_flags=list(bundle.flags),
        operator_summary=bundle.operator_summary,
        structured_facts=structured_facts,
        prompt_version=PROMPT_VERSION,
    )


def _build_structured_facts(*, bundle: OpportunityContextBundle) -> dict[str, object]:
    return {
        "candidate_posture": bundle.candidate.posture,
        "comparison_alignment": bundle.comparison.alignment,
        "candidate_score": bundle.candidate.candidate_score,
        "confidence_score": bundle.candidate.confidence_score,
        "conflict_score": bundle.candidate.conflict_score,
        "primary_market_slug": bundle.candidate.primary_market_slug,
        "primary_symbol": bundle.candidate.primary_symbol,
        "news_matched_article_count": bundle.news_evidence.matched_article_count,
        "news_official_source_present": bundle.news_evidence.official_source_present,
        "bundle_completeness_score": bundle.quality.completeness_score,
        "bundle_key_flags": list(bundle.flags[:_MAX_BUNDLE_FLAGS]),
    }
