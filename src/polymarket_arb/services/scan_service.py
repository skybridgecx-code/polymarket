from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from polymarket_arb.clients.clob import ClobClient
from polymarket_arb.clients.gamma import GammaClient
from polymarket_arb.config import Settings
from polymarket_arb.ingest.normalize import normalize_books, normalize_events
from polymarket_arb.models.normalized import NormalizedBook
from polymarket_arb.models.raw import RawClobBook


def _decimal_to_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.normalize(), "f")


class ScanService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def build_scan_rows(self, *, limit: int) -> list[dict[str, Any]]:
        gamma_client = GammaClient(self._settings)
        clob_client = ClobClient(self._settings)
        try:
            raw_events = await gamma_client.list_events(limit=max(limit * 5, 25))
            events = normalize_events(raw_events)[:limit]

            token_ids = sorted(
                {
                    token_id
                    for event in events
                    for market in event.markets
                    for token_id in market.token_ids
                }
            )

            raw_books = await self._fetch_books(clob_client, token_ids)
            books_by_token = {book.token_id: book for book in normalize_books(raw_books)}

            rows: list[dict[str, Any]] = []
            for event in events:
                rows.append(
                    {
                        "event_id": event.event_id,
                        "event_slug": event.slug,
                        "title": event.title,
                        "market_count": len(event.markets),
                        "markets": [
                            {
                                "market_id": market.market_id,
                                "question": market.question,
                                "token_ids": market.token_ids,
                                "books": [
                                    self._book_summary(token_id, books_by_token.get(token_id))
                                    for token_id in market.token_ids
                                ],
                            }
                            for market in event.markets
                        ],
                    }
                )
            return rows
        finally:
            await gamma_client.aclose()
            await clob_client.aclose()

    async def _fetch_books(self, client: ClobClient, token_ids: list[str]) -> list[RawClobBook]:
        results = await asyncio.gather(
            *(client.get_book(token_id) for token_id in token_ids),
            return_exceptions=True,
        )
        books: list[RawClobBook] = []
        for result in results:
            if isinstance(result, RawClobBook):
                books.append(result)
        return books

    def _book_summary(self, token_id: str, book: NormalizedBook | None) -> dict[str, Any]:
        if book is None:
            return {
                "token_id": token_id,
                "best_bid": None,
                "best_ask": None,
                "spread": None,
            }
        return {
            "token_id": token_id,
            "best_bid": _decimal_to_string(book.best_bid),
            "best_ask": _decimal_to_string(book.best_ask),
            "spread": _decimal_to_string(book.spread),
        }

