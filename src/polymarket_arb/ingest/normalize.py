from __future__ import annotations

from polymarket_arb.models.normalized import NormalizedBook, NormalizedEvent
from polymarket_arb.models.raw import RawClobBook, RawGammaEvent


def normalize_events(records: list[RawGammaEvent]) -> list[NormalizedEvent]:
    normalized = [NormalizedEvent.from_raw(record) for record in records]
    open_events = [event for event in normalized if event.markets]
    open_events.sort(key=lambda event: (event.slug, event.event_id))
    return open_events


def normalize_books(records: list[RawClobBook]) -> list[NormalizedBook]:
    books = [NormalizedBook.from_raw(record) for record in records]
    books.sort(key=lambda book: book.token_id)
    return books

