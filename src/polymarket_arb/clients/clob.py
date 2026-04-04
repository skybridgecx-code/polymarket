from __future__ import annotations

import httpx

from polymarket_arb.config import Settings
from polymarket_arb.models.raw import RawClobBook
from polymarket_arb.utils.time import utc_now


class ClobClient:
    def __init__(self, settings: Settings) -> None:
        self._client = httpx.AsyncClient(
            base_url=str(settings.clob_base_url),
            timeout=settings.request_timeout_seconds,
        )

    async def get_book(self, token_id: str) -> RawClobBook:
        response = await self._client.get("/book", params={"token_id": token_id})
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError(f"Expected dict payload from CLOB /book, got {type(payload)!r}")
        return RawClobBook(
            source="clob.book",
            fetched_at=utc_now(),
            token_id=token_id,
            payload=payload,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

