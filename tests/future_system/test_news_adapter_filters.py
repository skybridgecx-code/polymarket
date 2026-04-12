"""Filtering tests for deterministic news adapter exact-match criteria."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from future_system.news_adapter.filters import filter_news_records
from future_system.news_adapter.parser import parse_news_records

_FIXTURE_PATH = Path("tests/fixtures/future_system/news/raw_news_records.json")


def test_publisher_filter_works() -> None:
    records = _records()

    filtered = filter_news_records(records=records, publisher=" Reuters ")

    assert [record.article_id for record in filtered] == ["wire-001"]


def test_entity_filter_works() -> None:
    records = _records()

    filtered = filter_news_records(records=records, entity="BLACKROCK")

    assert [record.article_id for record in filtered] == ["newsroom-001"]


def test_topic_filter_works() -> None:
    records = _records()

    filtered = filter_news_records(records=records, topic="Derivatives")

    assert [record.article_id for record in filtered] == ["analysis-001"]


def test_official_source_filter_works() -> None:
    records = _records()

    filtered = filter_news_records(records=records, is_official_source=True)

    assert [record.article_id for record in filtered] == ["official-001"]


def test_published_at_cutoff_works() -> None:
    records = _records()

    filtered = filter_news_records(
        records=records,
        published_at_gte=datetime.fromisoformat("2026-04-10T16:00:00+00:00"),
    )

    assert [record.article_id for record in filtered] == ["newsroom-001", "analysis-001"]


def test_unmatched_filters_return_empty_list() -> None:
    records = _records()

    filtered = filter_news_records(records=records, publisher="No Publisher")

    assert filtered == []


def test_input_order_is_preserved_after_filtering() -> None:
    records = _records()

    filtered = filter_news_records(records=records, topic="crypto")

    assert [record.article_id for record in filtered] == [
        "official-001",
        "newsroom-001",
        "analysis-001",
    ]


def _records() -> list:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return parse_news_records(payload).records
