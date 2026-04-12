"""Deterministic assembler for canonical theme-linked news evidence packets."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from future_system.news_adapter.models import NormalizedNewsRecord
from future_system.news_evidence.models import (
    MatchedNewsEvidence,
    NewsEvidenceAssemblyError,
    ThemeNewsEvidencePacket,
)
from future_system.news_evidence.scoring import (
    compute_news_coverage_score,
    compute_news_freshness_score,
    compute_news_trust_score,
)
from future_system.theme_graph.models import ThemeLinkPacket

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class _MatchCandidate:
    record: NormalizedNewsRecord
    evidence: MatchedNewsEvidence


def assemble_theme_news_evidence_packet(
    *,
    theme_packet: ThemeLinkPacket,
    news_records: Sequence[NormalizedNewsRecord | Mapping[str, Any]],
    reference_time: datetime,
) -> ThemeNewsEvidencePacket:
    """Build deterministic theme-scoped news evidence from linked theme metadata."""

    linked_entities = _extract_linked_entities(theme_packet)
    if not linked_entities:
        raise NewsEvidenceAssemblyError(
            f"No linked news entities for theme {theme_packet.theme_id!r}."
        )
    linked_entity_set = set(linked_entities)
    theme_topic_tokens = _extract_theme_topic_tokens(theme_packet=theme_packet)

    matched_candidates: list[_MatchCandidate] = []
    observed_linked_entities: set[str] = set()

    for value in news_records:
        record = _normalize_news_record(value)
        match_reasons = _derive_match_reasons(
            record=record,
            linked_entities=linked_entity_set,
            theme_topic_tokens=theme_topic_tokens,
        )
        if not match_reasons:
            continue

        observed_linked_entities.update(
            entity for entity in record.entities if entity in linked_entity_set
        )

        freshness_score = compute_news_freshness_score(
            published_at=record.published_at,
            reference_time=reference_time,
        )
        evidence_flags = []
        if freshness_score <= 0.15:
            evidence_flags.append("stale_news_record")

        matched_candidates.append(
            _MatchCandidate(
                record=record,
                evidence=MatchedNewsEvidence(
                    article_id=record.article_id,
                    publisher=record.publisher,
                    source_type=record.source_type,
                    headline=record.headline,
                    published_at=record.published_at,
                    trust_score=record.trust_score,
                    freshness_score=freshness_score,
                    match_reasons=match_reasons,
                    entities=record.entities,
                    topics=record.topics,
                    flags=evidence_flags,
                    is_primary=False,
                ),
            )
        )

    if not matched_candidates:
        raise NewsEvidenceAssemblyError(
            f"No normalized news records matched linked entities/topics for "
            f"theme {theme_packet.theme_id!r}."
        )

    primary = _select_primary_record(matched_candidates)
    matched_records = [
        item.evidence.model_copy(update={"is_primary": item is primary})
        for item in matched_candidates
    ]

    matched_article_count = len(matched_records)
    freshness_score = round(
        sum(item.freshness_score for item in matched_records) / matched_article_count,
        3,
    )
    trust_score = compute_news_trust_score(
        trust_scores=[item.trust_score for item in matched_records]
    )
    coverage_score = compute_news_coverage_score(
        linked_entities=linked_entities,
        observed_linked_entities=sorted(observed_linked_entities),
    )

    official_source_present = any(item.record.is_official_source for item in matched_candidates)
    publishers = {item.record.publisher for item in matched_candidates}

    packet_flags: set[str] = set()
    if any("stale_news_record" in item.flags for item in matched_records):
        packet_flags.add("stale_news_evidence")
    if trust_score < 0.55:
        packet_flags.add("weak_news_trust")
    if coverage_score < 0.60:
        packet_flags.add("weak_news_coverage")
    if official_source_present:
        packet_flags.add("official_source_present")
    if len(publishers) == 1:
        packet_flags.add("single_source_only")
    if matched_article_count == 1:
        packet_flags.add("single_article_match")

    ordered_flags = sorted(packet_flags)
    flag_text = "none" if not ordered_flags else ",".join(ordered_flags)
    official_text = "true" if official_source_present else "false"
    explanation = (
        f"matched_article_count={matched_article_count}; "
        f"primary_article_id={primary.evidence.article_id}; "
        f"freshness_score={freshness_score:.3f}; "
        f"trust_score={trust_score:.3f}; "
        f"coverage_score={coverage_score:.3f}; "
        f"official_source_present={official_text}; "
        f"flags={flag_text}."
    )

    return ThemeNewsEvidencePacket(
        theme_id=theme_packet.theme_id,
        primary_article_id=primary.evidence.article_id,
        matched_records=matched_records,
        matched_article_count=matched_article_count,
        freshness_score=freshness_score,
        trust_score=trust_score,
        coverage_score=coverage_score,
        official_source_present=official_source_present,
        flags=ordered_flags,
        explanation=explanation,
    )


def _normalize_news_record(
    value: NormalizedNewsRecord | Mapping[str, Any],
) -> NormalizedNewsRecord:
    if isinstance(value, NormalizedNewsRecord):
        return value
    try:
        return NormalizedNewsRecord.model_validate(value)
    except (ValidationError, ValueError, TypeError) as exc:
        raise NewsEvidenceAssemblyError("Invalid normalized news record payload.") from exc


def _extract_linked_entities(theme_packet: ThemeLinkPacket) -> list[str]:
    seen: set[str] = set()
    linked: list[str] = []
    for entity in theme_packet.matched_entities:
        token = _normalize_match_token(entity.entity_name)
        if not token or token in seen:
            continue
        seen.add(token)
        linked.append(token)
    return linked


def _extract_theme_topic_tokens(*, theme_packet: ThemeLinkPacket) -> set[str]:
    text_parts = [theme_packet.theme_id]
    text_parts.extend(entity.entity_name for entity in theme_packet.matched_entities)

    for market in theme_packet.matched_polymarket_markets:
        if market.market_slug is not None:
            text_parts.append(market.market_slug)
        if market.event_slug is not None:
            text_parts.append(market.event_slug)

    return _tokenize_text(" ".join(text_parts))


def _derive_match_reasons(
    *,
    record: NormalizedNewsRecord,
    linked_entities: set[str],
    theme_topic_tokens: set[str],
) -> list[str]:
    reasons: list[str] = []

    entity_overlap = any(entity in linked_entities for entity in record.entities)
    if entity_overlap:
        reasons.append("entity_match")

    topic_overlap = _topic_overlap(record.topics, theme_topic_tokens)
    if topic_overlap:
        reasons.append("topic_match")

    if record.is_official_source and reasons:
        reasons.append("official_source_match")

    return reasons


def _topic_overlap(record_topics: Sequence[str], theme_topic_tokens: set[str]) -> bool:
    if not record_topics or not theme_topic_tokens:
        return False

    for topic in record_topics:
        normalized_topic = _normalize_match_token(topic)
        if normalized_topic in theme_topic_tokens:
            return True
        if _tokenize_text(normalized_topic) & theme_topic_tokens:
            return True
    return False


def _select_primary_record(candidates: Sequence[_MatchCandidate]) -> _MatchCandidate:
    return sorted(
        candidates,
        key=lambda item: (
            0 if item.record.is_official_source else 1,
            -item.evidence.trust_score,
            -_to_epoch_seconds(item.evidence.published_at),
            item.evidence.article_id,
        ),
    )[0]


def _normalize_match_token(value: str) -> str:
    return " ".join(value.split()).casefold()


def _tokenize_text(value: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(value.casefold()) if token}


def _to_epoch_seconds(value: datetime) -> float:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC).timestamp()
    return value.astimezone(UTC).timestamp()
