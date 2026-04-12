"""Parser behavior tests for deterministic news adapter normalization."""

from __future__ import annotations

import json
from pathlib import Path

from future_system.news_adapter.parser import parse_news_records

_FIXTURE_PATH = Path("tests/fixtures/future_system/news/raw_news_records.json")


def test_fixture_parses_into_normalized_news_records() -> None:
    payload = _load_fixture_payload()

    result = parse_news_records(payload)

    assert len(result.records) == 4
    assert result.publisher_count == 4
    assert [record.article_id for record in result.records] == [
        "wire-001",
        "official-001",
        "newsroom-001",
        "analysis-001",
    ]


def test_malformed_records_increase_skipped_records() -> None:
    payload = _load_fixture_payload()

    result = parse_news_records(payload)

    assert result.skipped_records == 1
    assert result.flags == ["skipped_invalid_records"]


def test_multiple_source_types_are_supported() -> None:
    payload = _load_fixture_payload()

    result = parse_news_records(payload)

    assert {record.source_type for record in result.records} == {
        "wire",
        "official",
        "newsroom",
        "analysis",
    }


def test_parser_flags_are_deterministic() -> None:
    payload = _load_fixture_payload()

    first = parse_news_records(payload)
    second = parse_news_records(payload)

    assert first.model_dump() == second.model_dump()


def test_entity_topic_normalization_is_deterministic() -> None:
    payload = _load_fixture_payload()

    result = parse_news_records(payload)
    reuters = result.records[0]

    assert reuters.publisher == "reuters"
    assert reuters.entities == ["federal reserve", "jerome powell"]
    assert reuters.topics == ["macro", "rates"]


def _load_fixture_payload() -> list[dict[str, object]]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
