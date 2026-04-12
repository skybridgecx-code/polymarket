"""Assembler behavior tests for deterministic theme-linked news evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from future_system.news_evidence.assembler import assemble_theme_news_evidence_packet
from future_system.news_evidence.models import NewsEvidenceAssemblyError
from future_system.theme_graph.models import ThemeLinkPacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/news/theme_news_records.json")
_REFERENCE_TIME = datetime(2026, 4, 11, 12, 0, tzinfo=UTC)


def test_linked_news_records_are_selected_correctly() -> None:
    packet = _theme_packet(entities=["SEC", "Federal Reserve", "Bank of Japan"])

    evidence = assemble_theme_news_evidence_packet(
        theme_packet=packet,
        news_records=_fixture_records(),
        reference_time=_REFERENCE_TIME,
    )

    assert [item.article_id for item in evidence.matched_records] == [
        "official-001",
        "wire-001",
        "newsroom-001",
    ]


def test_unmatched_records_are_excluded() -> None:
    packet = _theme_packet(entities=["SEC", "Federal Reserve", "Bank of Japan"])

    evidence = assemble_theme_news_evidence_packet(
        theme_packet=packet,
        news_records=_fixture_records(),
        reference_time=_REFERENCE_TIME,
    )

    matched_ids = {item.article_id for item in evidence.matched_records}
    assert "analysis-001" not in matched_ids
    assert "other-001" not in matched_ids


def test_no_matches_raises_news_evidence_assembly_error() -> None:
    packet = _theme_packet(
        theme_id="theme_unrelated_signal",
        entities=["Bank of Japan"],
        include_market_links=False,
    )

    with pytest.raises(NewsEvidenceAssemblyError):
        assemble_theme_news_evidence_packet(
            theme_packet=packet,
            news_records=_fixture_records(),
            reference_time=_REFERENCE_TIME,
        )


def test_no_linked_news_entities_raises_news_evidence_assembly_error() -> None:
    packet = _theme_packet(entities=[])

    with pytest.raises(NewsEvidenceAssemblyError):
        assemble_theme_news_evidence_packet(
            theme_packet=packet,
            news_records=_fixture_records(),
            reference_time=_REFERENCE_TIME,
        )


def test_primary_record_selection_is_deterministic() -> None:
    packet = _theme_packet(entities=["SEC", "Federal Reserve", "Bank of Japan"])

    first = assemble_theme_news_evidence_packet(
        theme_packet=packet,
        news_records=_fixture_records(),
        reference_time=_REFERENCE_TIME,
    )
    second = assemble_theme_news_evidence_packet(
        theme_packet=packet,
        news_records=_fixture_records(),
        reference_time=_REFERENCE_TIME,
    )

    assert first.model_dump() == second.model_dump()
    assert first.primary_article_id == "official-001"
    assert [
        item.article_id for item in first.matched_records if item.is_primary
    ] == ["official-001"]


def test_coverage_score_is_deterministic() -> None:
    packet = _theme_packet(entities=["SEC", "Federal Reserve", "Bank of Japan"])

    evidence = assemble_theme_news_evidence_packet(
        theme_packet=packet,
        news_records=_fixture_records(),
        reference_time=_REFERENCE_TIME,
    )

    assert evidence.coverage_score == 0.667


def test_stale_weak_coverage_and_official_flags_surface_correctly() -> None:
    packet = _theme_packet(
        entities=["SEC", "Federal Reserve", "Bank of Japan", "ECB", "UK Treasury"]
    )

    evidence = assemble_theme_news_evidence_packet(
        theme_packet=packet,
        news_records=_fixture_records(),
        reference_time=_REFERENCE_TIME,
    )

    assert "stale_news_evidence" in evidence.flags
    assert "weak_news_coverage" in evidence.flags
    assert "official_source_present" in evidence.flags


def test_explanation_string_is_deterministic() -> None:
    packet = _theme_packet(entities=["SEC", "Federal Reserve", "Bank of Japan"])

    evidence = assemble_theme_news_evidence_packet(
        theme_packet=packet,
        news_records=_fixture_records(),
        reference_time=_REFERENCE_TIME,
    )

    assert evidence.explanation == (
        "matched_article_count=3; "
        "primary_article_id=official-001; "
        "freshness_score=0.650; "
        "trust_score=0.797; "
        "coverage_score=0.667; "
        "official_source_present=true; "
        "flags=official_source_present,stale_news_evidence."
    )


def _fixture_records() -> list[dict[str, object]]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _theme_packet(
    *,
    theme_id: str = "theme_crypto_regulation_signal",
    entities: list[str],
    include_market_links: bool = True,
) -> ThemeLinkPacket:
    return ThemeLinkPacket.model_validate(
        {
            "theme_id": theme_id,
            "matched_polymarket_markets": (
                [
                    {
                        "condition_id": "0xtheme18j",
                        "market_slug": "crypto-regulation-signal",
                        "event_slug": "regulation-monitoring",
                        "outcome_map": {"Yes": "yes", "No": "no"},
                        "confidence": 0.9,
                        "link_basis": "manual",
                        "notes": "Fixture theme link for news evidence tests.",
                    }
                ]
                if include_market_links
                else []
            ),
            "matched_assets": [],
            "matched_entities": [
                {
                    "entity_name": entity,
                    "entity_type": "institution",
                    "relevance": 0.8,
                    "required": True,
                }
                for entity in entities
            ],
            "ambiguity_flags": [],
            "confidence_score": 0.88,
            "explanation": "Fixture theme packet for deterministic news evidence tests.",
        }
    )
