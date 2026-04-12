"""Validation tests for future_system.news_adapter models."""

from __future__ import annotations

import pytest
from future_system.news_adapter.models import NormalizedNewsRecord
from pydantic import ValidationError


def test_normalized_news_record_accepts_valid_payload() -> None:
    record = NormalizedNewsRecord.model_validate(_valid_payload())

    assert record.publisher == "reuters"
    assert record.article_id == "wire-001"
    assert record.headline == "Fed Signals No Immediate Rate Cut"
    assert record.entities == ["federal reserve", "jerome powell"]
    assert record.topics == ["macro", "rates"]


def test_invalid_trust_score_is_rejected() -> None:
    invalid = _valid_payload()
    invalid["trust_score"] = 1.01

    with pytest.raises(ValidationError):
        NormalizedNewsRecord.model_validate(invalid)


def test_required_string_fields_are_enforced() -> None:
    invalid_publisher = _valid_payload()
    invalid_publisher["publisher"] = "   "

    with pytest.raises(ValidationError):
        NormalizedNewsRecord.model_validate(invalid_publisher)

    invalid_article_id = _valid_payload()
    invalid_article_id["article_id"] = ""

    with pytest.raises(ValidationError):
        NormalizedNewsRecord.model_validate(invalid_article_id)

    invalid_headline = _valid_payload()
    invalid_headline["headline"] = ""

    with pytest.raises(ValidationError):
        NormalizedNewsRecord.model_validate(invalid_headline)


def test_entity_and_topic_normalization_is_enforced() -> None:
    payload = _valid_payload()
    payload["entities"] = [" Ethereum ", "ethereum", "Deribit"]
    payload["topics"] = ["Crypto", "crypto", " Derivatives "]

    record = NormalizedNewsRecord.model_validate(payload)

    assert record.entities == ["ethereum", "deribit"]
    assert record.topics == ["crypto", "derivatives"]


def _valid_payload() -> dict[str, object]:
    return {
        "source": "fixture",
        "publisher": "Reuters",
        "source_type": "wire",
        "article_id": "wire-001",
        "headline": "Fed Signals No Immediate Rate Cut",
        "summary": "A summary.",
        "url": "https://example.com/reuters/fed-rates",
        "published_at": "2026-04-10T14:00:00Z",
        "ingested_at": "2026-04-10T14:05:00Z",
        "entities": ["Federal Reserve", "federal reserve", "Jerome Powell"],
        "topics": ["Macro", "Rates", "macro"],
        "trust_score": 0.88,
        "language": "EN",
        "is_official_source": False,
    }
