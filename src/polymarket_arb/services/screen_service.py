from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any

from polymarket_arb.clients.clob import ClobClient
from polymarket_arb.clients.gamma import GammaClient
from polymarket_arb.config import Settings
from polymarket_arb.ingest.normalize import normalize_books, normalize_events
from polymarket_arb.models.raw import RawClobBook


class ScreenService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def build_screen_rows(
        self,
        *,
        limit: int,
        min_spread: float = 0.02,
    ) -> list[dict[str, Any]]:
        gamma_client = GammaClient(self._settings)
        clob_client = ClobClient(self._settings)
        try:
            raw_events = await gamma_client.list_events(limit=max(limit * 5, 50))
            events = normalize_events(raw_events)

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

            threshold = Decimal(str(min_spread))
            rows_with_spread: list[tuple[Decimal, dict[str, Any]]] = []

            for event in events:
                for market in event.markets:
                    if len(market.outcomes) != 2 or len(market.token_ids) != 2:
                        continue

                    yes_token_id = market.token_ids[0]
                    no_token_id = market.token_ids[1]
                    yes_book = books_by_token.get(yes_token_id)
                    no_book = books_by_token.get(no_token_id)

                    if yes_book is None or no_book is None:
                        continue

                    spread = yes_book.spread
                    if spread is None:
                        continue

                    row = {
                        "event_slug": event.slug,
                        "question": market.question,
                        "market_id": market.market_id,
                        "yes_best_bid": (
                            str(yes_book.best_bid)
                            if yes_book.best_bid is not None
                            else "none"
                        ),
                        "yes_best_ask": (
                            str(yes_book.best_ask)
                            if yes_book.best_ask is not None
                            else "none"
                        ),
                        "no_best_bid": (
                            str(no_book.best_bid)
                            if no_book.best_bid is not None
                            else "none"
                        ),
                        "no_best_ask": (
                            str(no_book.best_ask)
                            if no_book.best_ask is not None
                            else "none"
                        ),
                        "spread": str(spread),
                        "midpoint": (
                            str(yes_book.midpoint)
                            if yes_book.midpoint is not None
                            else "none"
                        ),
                        "accepting_orders": market.accepting_orders,
                    }

                    if row["accepting_orders"] and spread >= threshold:
                        rows_with_spread.append((spread, row))

            rows_with_spread.sort(key=lambda item: item[0], reverse=True)
            return [row for _, row in rows_with_spread[:limit]]
        finally:
            await gamma_client.aclose()
            await clob_client.aclose()

    async def _fetch_in_batches(
        self,
        token_ids: list[str],
        fetch_fn: Callable[[str], Awaitable[Any]],
    ) -> list[Any]:
        results: list[Any] = []
        batch_size = 10

        for start in range(0, len(token_ids), batch_size):
            batch = token_ids[start : start + batch_size]
            batch_results = await asyncio.gather(
                *(fetch_fn(token_id) for token_id in batch),
                return_exceptions=True,
            )
            for result in batch_results:
                if not isinstance(result, BaseException):
                    results.append(result)

            if start + batch_size < len(token_ids):
                await asyncio.sleep(0.5)

        return results

    async def _fetch_books(self, client: ClobClient, token_ids: list[str]) -> list[RawClobBook]:
        results = await self._fetch_in_batches(token_ids, client.get_book)
        books: list[RawClobBook] = []
        for result in results:
            if isinstance(result, RawClobBook):
                books.append(result)
        return books
