from __future__ import annotations

import httpx

from polymarket_arb.config import Settings
from polymarket_arb.models.raw import RawGammaEvent
from polymarket_arb.utils.time import utc_now


class GammaClient:
    def __init__(self, settings: Settings) -> None:
        self._client = httpx.AsyncClient(
            base_url=str(settings.gamma_base_url),
            timeout=settings.request_timeout_seconds,
        )

    async def list_events(
        self,
        *,
        limit: int,
        active: bool = True,
        closed: bool = False,
        archived: bool = False,
    ) -> list[RawGammaEvent]:
        response = await self._client.get(
            "/events",
            params={
                "limit": limit,
                "active": str(active).lower(),
                "closed": str(closed).lower(),
                "archived": str(archived).lower(),
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise TypeError(f"Expected list payload from Gamma /events, got {type(payload)!r}")

        fetched_at = utc_now()
        return [
            RawGammaEvent(source="gamma.events", fetched_at=fetched_at, payload=item)
            for item in payload
            if isinstance(item, dict)
        ]

    async def aclose(self) -> None:
        await self._client.aclose()
