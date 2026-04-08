from __future__ import annotations

import asyncio
from typing import Any

from polymarket_arb.clients.clob import ClobClient
from polymarket_arb.clients.gamma import GammaClient
from polymarket_arb.config import Settings
from polymarket_arb.ingest.normalize import normalize_books, normalize_events, normalize_fee_rates
from polymarket_arb.models.raw import RawClobBook, RawClobFeeRate
from polymarket_arb.opportunities.engine import OpportunityEngine


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
            raw_fee_rates = await self._fetch_fee_rates(clob_client, token_ids)
            books_by_token = {book.token_id: book for book in normalize_books(raw_books)}
            fee_rates_by_token = {
                fee_rate.token_id: fee_rate for fee_rate in normalize_fee_rates(raw_fee_rates)
            }

            candidates = OpportunityEngine().build_candidates(
                events=events,
                books_by_token=books_by_token,
                fee_rates_by_token=fee_rates_by_token,
            )
            return [candidate.to_output() for candidate in candidates]
        finally:
            await gamma_client.aclose()
            await clob_client.aclose()

    async def _fetch_in_batches(self, token_ids: list[str], fetch_fn) -> list:
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

    async def _fetch_fee_rates(
        self,
        client: ClobClient,
        token_ids: list[str],
    ) -> list[RawClobFeeRate]:
        results = await self._fetch_in_batches(token_ids, client.get_fee_rate)
        fee_rates: list[RawClobFeeRate] = []
        for result in results:
            if isinstance(result, RawClobFeeRate):
                fee_rates.append(result)
        return fee_rates
