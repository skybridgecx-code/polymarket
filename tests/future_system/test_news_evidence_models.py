"""Model validation tests for future_system.news_evidence contracts."""

from __future__ import annotations

import pytest
from future_system.news_evidence.models import MatchedNewsEvidence, ThemeNewsEvidencePacket
from pydantic import ValidationError


def test_news_evidence_models_accept_valid_payloads() -> None:
    matched = MatchedNewsEvidence.model_validate(
        {
            "article_id": "official-001",
            "publisher": "SEC",
            "source_type": "official",
            "headline": "SEC Updates Digital Asset Guidance",
            "published_at": "2026-04-11T11:30:00Z",
            "trust_score": 0.92,
            "freshness_score": 1.0,
            "match_reasons": ["entity_match", "official_source_match"],
            "entities": ["SEC", "Digital Assets", "sec"],
            "topics": ["Regulation", "Crypto", "regulation"],
            "flags": [],
            "is_primary": True,
        }
    )
    packet = ThemeNewsEvidencePacket.model_validate(
        {
            "theme_id": "theme_crypto_regulation_signal",
            "primary_article_id": "official-001",
            "matched_records": [matched.model_dump()],
            "matched_article_count": 1,
            "freshness_score": 1.0,
            "trust_score": 0.92,
            "coverage_score": 0.5,
            "official_source_present": True,
            "flags": ["official_source_present"],
            "explanation": "Deterministic news evidence packet.",
        }
    )

    assert matched.publisher == "sec"
    assert matched.entities == ["sec", "digital assets"]
    assert matched.topics == ["regulation", "crypto"]
    assert packet.primary_article_id == "official-001"


def test_news_evidence_models_reject_invalid_bounded_scores() -> None:
    with pytest.raises(ValidationError):
        MatchedNewsEvidence.model_validate(
            {
                "article_id": "wire-001",
                "publisher": "reuters",
                "source_type": "wire",
                "headline": "Invalid trust score",
                "published_at": "2026-04-11T07:00:00Z",
                "trust_score": 1.2,
                "freshness_score": 0.8,
                "match_reasons": ["entity_match"],
                "entities": ["federal reserve"],
                "topics": ["macro"],
                "flags": [],
                "is_primary": False,
            }
        )

    with pytest.raises(ValidationError):
        ThemeNewsEvidencePacket.model_validate(
            {
                "theme_id": "theme_bad",
                "primary_article_id": "wire-001",
                "matched_records": [],
                "matched_article_count": 0,
                "freshness_score": 0.4,
                "trust_score": 0.6,
                "coverage_score": 1.2,
                "official_source_present": False,
                "flags": [],
                "explanation": "Invalid coverage score.",
            }
        )


def test_news_evidence_models_enforce_required_fields() -> None:
    with pytest.raises(ValidationError):
        MatchedNewsEvidence.model_validate(
            {
                "article_id": "",
                "publisher": "sec",
                "source_type": "official",
                "headline": "Missing article id",
                "published_at": "2026-04-11T11:30:00Z",
                "trust_score": 0.9,
                "freshness_score": 0.9,
                "match_reasons": ["entity_match"],
                "entities": ["sec"],
                "topics": ["regulation"],
                "flags": [],
                "is_primary": False,
            }
        )

    with pytest.raises(ValidationError):
        ThemeNewsEvidencePacket.model_validate(
            {
                "theme_id": "   ",
                "primary_article_id": None,
                "matched_records": [],
                "matched_article_count": 0,
                "freshness_score": 0.5,
                "trust_score": 0.5,
                "coverage_score": 0.5,
                "official_source_present": False,
                "flags": [],
                "explanation": "Missing theme id.",
            }
        )
