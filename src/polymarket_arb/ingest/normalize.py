from __future__ import annotations

from polymarket_arb.models.normalized import NormalizedBook, NormalizedEvent, NormalizedFeeRate
from polymarket_arb.models.raw import RawClobBook, RawClobFeeRate, RawGammaEvent


def normalize_events(records: list[RawGammaEvent]) -> list[NormalizedEvent]:
    normalized = [NormalizedEvent.from_raw(record) for record in records]
    open_events = [event for event in normalized if event.markets]
    open_events.sort(key=lambda event: (event.slug, event.event_id))
    return open_events


def normalize_books(records: list[RawClobBook]) -> list[NormalizedBook]:
    books = [NormalizedBook.from_raw(record) for record in records]
    books.sort(key=lambda book: book.token_id)
    return books


def normalize_fee_rates(records: list[RawClobFeeRate]) -> list[NormalizedFeeRate]:
    fee_rates = [NormalizedFeeRate.from_raw(record) for record in records]
    fee_rates.sort(key=lambda fee_rate: fee_rate.token_id)
    return fee_rates
