from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from polymarket_arb.ingest.normalize import normalize_books, normalize_events
from polymarket_arb.models.raw import RawClobBook, RawGammaEvent


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_normalize_events_filters_closed_markets_and_parses_tokens() -> None:
    fixture_path = Path("tests/fixtures/api/gamma/events_sample.json")
    payload = _load_json(fixture_path)
    assert isinstance(payload, list)

    records = [
        RawGammaEvent(
            source="gamma.events",
            fetched_at=datetime(2026, 4, 4, tzinfo=UTC),
            payload=payload[0],
        )
    ]

    events = normalize_events(records)

    assert len(events) == 1
    assert events[0].slug == "microstrategy-sell-any-bitcoin-in-2025"
    assert len(events[0].markets) == 1
    market = events[0].markets[0]
    assert market.market_id == "824952"
    assert market.outcomes == ["Yes", "No"]
    assert market.token_ids == [
        "111128191581505463501777127559667396812474366956707382672202929745167742497287",
        "99807503632459517030616292055983105381849115736225256331133222076990620978808",
    ]


def test_normalize_books_sorts_asks_and_computes_summary_fields() -> None:
    fixture_path = Path("tests/fixtures/api/clob/book_sample.json")
    payload = _load_json(fixture_path)
    assert isinstance(payload, dict)

    records = [
        RawClobBook(
            source="clob.book",
            fetched_at=datetime(2026, 4, 4, tzinfo=UTC),
            token_id="111128191581505463501777127559667396812474366956707382672202929745167742497287",
            payload=payload,
        )
    ]

    books = normalize_books(records)

    assert len(books) == 1
    book = books[0]
    assert book.best_bid == Decimal("0.12")
    assert book.best_ask == Decimal("0.4")
    assert book.spread == Decimal("0.28")
    assert [level.price for level in book.asks] == [
        Decimal("0.4"),
        Decimal("0.56"),
        Decimal("0.99"),
    ]
