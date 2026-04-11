"""Deterministic linker that emits canonical theme link packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from future_system.theme_graph.matcher import match_theme_candidates
from future_system.theme_graph.models import (
    NormalizedPolymarketMetadata,
    ThemeDefinition,
    ThemeLinkPacket,
    ThemeMatchResult,
)
from future_system.theme_graph.registry import ThemeRegistry


def build_theme_link_packet(match_result: ThemeMatchResult) -> ThemeLinkPacket | None:
    """Build a deterministic link packet from a confident theme match."""

    candidate = match_result.confident_candidate
    if candidate is None:
        return None

    theme = candidate.theme
    packet_confidence = _packet_confidence(candidate.score, match_result.ambiguity_flags)
    reason_text = ", ".join(candidate.reasons) if candidate.reasons else "deterministic_match"
    ambiguity_text = (
        "none"
        if not match_result.ambiguity_flags
        else ", ".join(match_result.ambiguity_flags)
    )
    explanation = (
        f"Matched theme {theme.theme_id} via {reason_text}; "
        f"candidate_score={candidate.score:.3f}; ambiguity={ambiguity_text}."
    )

    return ThemeLinkPacket(
        theme_id=theme.theme_id,
        matched_polymarket_markets=list(candidate.matched_polymarket_markets),
        matched_assets=list(theme.asset_links),
        matched_entities=list(theme.news_entities),
        ambiguity_flags=list(match_result.ambiguity_flags),
        confidence_score=packet_confidence,
        explanation=explanation,
    )


def link_market_to_theme_packet(
    market_metadata: NormalizedPolymarketMetadata | Mapping[str, Any] | object,
    themes: Sequence[ThemeDefinition] | ThemeRegistry,
) -> ThemeLinkPacket | None:
    """Convenience wrapper that matches then links in one deterministic step."""

    match_result = match_theme_candidates(market_metadata=market_metadata, themes=themes)
    return build_theme_link_packet(match_result)


def _packet_confidence(score: float, ambiguity_flags: list[str]) -> float:
    penalty = 0.10 * len(ambiguity_flags)
    adjusted = max(0.0, score - penalty)
    return round(adjusted, 3)
