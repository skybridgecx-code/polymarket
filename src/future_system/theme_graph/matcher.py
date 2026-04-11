"""Deterministic candidate matcher for Polymarket metadata to canonical themes."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from future_system.theme_graph.models import (
    NormalizedPolymarketMetadata,
    PolymarketThemeLink,
    ThemeDefinition,
    ThemeMatchCandidate,
    ThemeMatchResult,
)
from future_system.theme_graph.registry import ThemeRegistry

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the",
    "and",
    "for",
    "will",
    "with",
    "from",
    "this",
    "that",
    "into",
    "about",
    "than",
    "over",
    "under",
}

DEFAULT_MINIMUM_SCORE = 0.35
DEFAULT_STRONG_SCORE = 0.75
DEFAULT_AMBIGUITY_MARGIN = 0.05


def match_theme_candidates(
    market_metadata: NormalizedPolymarketMetadata | Mapping[str, Any] | object,
    themes: Sequence[ThemeDefinition] | ThemeRegistry,
    *,
    minimum_score: float = DEFAULT_MINIMUM_SCORE,
    strong_score: float = DEFAULT_STRONG_SCORE,
    ambiguity_margin: float = DEFAULT_AMBIGUITY_MARGIN,
) -> ThemeMatchResult:
    """Match normalized Polymarket metadata to ranked theme candidates."""

    market = _coerce_market_metadata(market_metadata)
    resolved_themes = _coerce_themes(themes)

    candidates: list[ThemeMatchCandidate] = []
    for theme in resolved_themes:
        candidate = _score_theme_candidate(market, theme)
        if candidate is None:
            continue
        if candidate.score < minimum_score:
            continue
        candidates.append(candidate)

    sorted_candidates = sorted(
        candidates,
        key=lambda candidate: (-candidate.score, candidate.theme.theme_id),
    )

    confident_candidate = (
        sorted_candidates[0]
        if sorted_candidates and sorted_candidates[0].score >= strong_score
        else None
    )

    return ThemeMatchResult(
        market=market,
        candidates=sorted_candidates,
        confident_candidate=confident_candidate,
        ambiguity_flags=_ambiguity_flags(
            candidates=sorted_candidates,
            strong_score=strong_score,
            ambiguity_margin=ambiguity_margin,
        ),
    )


def _coerce_themes(themes: Sequence[ThemeDefinition] | ThemeRegistry) -> list[ThemeDefinition]:
    if isinstance(themes, ThemeRegistry):
        return themes.list_all()
    return list(themes)


def _coerce_market_metadata(
    market_metadata: NormalizedPolymarketMetadata | Mapping[str, Any] | object,
) -> NormalizedPolymarketMetadata:
    if isinstance(market_metadata, NormalizedPolymarketMetadata):
        return market_metadata
    if isinstance(market_metadata, Mapping):
        return NormalizedPolymarketMetadata.model_validate(dict(market_metadata))

    payload = {
        "market_slug": getattr(market_metadata, "market_slug", None),
        "event_slug": getattr(market_metadata, "event_slug", None),
        "question": getattr(market_metadata, "question", None),
        "description": getattr(market_metadata, "description", None),
        "condition_id": getattr(market_metadata, "condition_id", None),
    }
    return NormalizedPolymarketMetadata.model_validate(payload)


def _score_theme_candidate(
    market: NormalizedPolymarketMetadata,
    theme: ThemeDefinition,
) -> ThemeMatchCandidate | None:
    direct_score, matched_links, reasons = _direct_link_score(market, theme)
    if direct_score > 0.0:
        return ThemeMatchCandidate(
            theme=theme,
            score=round(direct_score, 3),
            reasons=reasons,
            matched_polymarket_markets=matched_links,
        )

    text_score, text_reasons = _text_overlap_score(market, theme)
    if text_score <= 0.0:
        return None
    return ThemeMatchCandidate(
        theme=theme,
        score=round(text_score, 3),
        reasons=text_reasons,
        matched_polymarket_markets=[],
    )


def _direct_link_score(
    market: NormalizedPolymarketMetadata,
    theme: ThemeDefinition,
) -> tuple[float, list[PolymarketThemeLink], list[str]]:
    best_score = 0.0
    best_links: list[PolymarketThemeLink] = []
    best_reasons: list[str] = []

    for link in theme.polymarket_links:
        score, reasons = _score_single_link(market, link)
        if score <= 0.0:
            continue
        if score > best_score:
            best_score = score
            best_links = [link]
            best_reasons = reasons
        elif score == best_score:
            best_links.append(link)
            best_reasons = _merge_reasons(best_reasons, reasons)

    return best_score, best_links, best_reasons


def _score_single_link(
    market: NormalizedPolymarketMetadata,
    link: PolymarketThemeLink,
) -> tuple[float, list[str]]:
    condition_match = _normalized_equal(market.condition_id, link.condition_id)
    market_slug_match = _normalized_equal(market.market_slug, link.market_slug)
    event_slug_match = _normalized_equal(market.event_slug, link.event_slug)

    reasons: list[str] = []
    if condition_match:
        reasons.append("condition_id_exact")
    if market_slug_match:
        reasons.append("market_slug_exact")
    if event_slug_match:
        reasons.append("event_slug_exact")

    if condition_match:
        return 1.0, reasons
    if market_slug_match and event_slug_match:
        return 0.95, reasons
    if market_slug_match:
        return 0.90, reasons
    if event_slug_match:
        return 0.80, reasons
    return 0.0, []


def _text_overlap_score(
    market: NormalizedPolymarketMetadata,
    theme: ThemeDefinition,
) -> tuple[float, list[str]]:
    market_tokens = _tokenize(
        " ".join(
            value
            for value in (
                market.question,
                market.description,
                market.market_slug,
                market.event_slug,
            )
            if value
        )
    )
    if not market_tokens:
        return 0.0, []

    theme_tokens = _tokenize(
        " ".join([theme.title, theme.primary_question, *theme.aliases])
    )
    if not theme_tokens:
        return 0.0, []

    shared_tokens = market_tokens & theme_tokens
    if len(shared_tokens) < 2:
        return 0.0, []

    theme_overlap = len(shared_tokens) / len(theme_tokens)
    market_overlap = len(shared_tokens) / len(market_tokens)
    if theme_overlap < 0.20 and market_overlap < 0.20:
        return 0.0, []

    score = min(0.69, 0.30 + (theme_overlap * 0.24) + (market_overlap * 0.20))
    return score, [f"text_overlap:{len(shared_tokens)}"]


def _ambiguity_flags(
    *,
    candidates: Sequence[ThemeMatchCandidate],
    strong_score: float,
    ambiguity_margin: float,
) -> list[str]:
    strong_candidates = [candidate for candidate in candidates if candidate.score >= strong_score]
    if len(strong_candidates) < 2:
        return []

    highest_score = strong_candidates[0].score
    competing = [
        candidate.theme.theme_id
        for candidate in strong_candidates
        if highest_score - candidate.score <= ambiguity_margin
    ]
    if len(competing) < 2:
        return []

    return [f"multiple_strong_matches:{','.join(competing)}"]


def _normalized_equal(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return False
    return _normalize_key(left) == _normalize_key(right)


def _normalize_key(value: str) -> str:
    return value.strip().casefold()


def _tokenize(text: str) -> set[str]:
    tokens = set()
    for token in _TOKEN_RE.findall(text.casefold()):
        if len(token) < 3:
            continue
        if token in _STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _merge_reasons(existing: list[str], incoming: list[str]) -> list[str]:
    merged: list[str] = []
    for reason in [*existing, *incoming]:
        if reason not in merged:
            merged.append(reason)
    return merged
