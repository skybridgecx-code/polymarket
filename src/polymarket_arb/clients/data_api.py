from __future__ import annotations

import httpx

from polymarket_arb.config import Settings
from polymarket_arb.models.raw import (
    RawDataLeaderboardEntry,
    RawDataTopHolderGroup,
    RawDataUserActivity,
)
from polymarket_arb.utils.time import utc_now


class DataApiClient:
    def __init__(self, settings: Settings) -> None:
        self._client = httpx.AsyncClient(
            base_url=str(settings.data_base_url),
            timeout=settings.request_timeout_seconds,
        )

    async def get_leaderboard(
        self,
        *,
        limit: int,
        time_period: str = "DAY",
        order_by: str = "VOL",
    ) -> list[RawDataLeaderboardEntry]:
        response = await self._client.get(
            "/v1/leaderboard",
            params={
                "limit": limit,
                "timePeriod": time_period,
                "orderBy": order_by,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise TypeError(
                f"Expected list payload from Data API /v1/leaderboard, got {type(payload)!r}"
            )

        fetched_at = utc_now()
        return [
            RawDataLeaderboardEntry(
                source="data_api.leaderboard",
                fetched_at=fetched_at,
                time_period=time_period,
                order_by=order_by,
                payload=item,
            )
            for item in payload
            if isinstance(item, dict)
        ]

    async def get_holders(
        self,
        *,
        condition_ids: list[str],
        limit: int,
    ) -> list[RawDataTopHolderGroup]:
        response = await self._client.get(
            "/holders",
            params={
                "market": ",".join(condition_ids),
                "limit": limit,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise TypeError(f"Expected list payload from Data API /holders, got {type(payload)!r}")

        fetched_at = utc_now()
        return [
            RawDataTopHolderGroup(
                source="data_api.holders",
                fetched_at=fetched_at,
                condition_ids=condition_ids,
                payload=item,
            )
            for item in payload
            if isinstance(item, dict)
        ]

    async def get_user_activity(
        self,
        *,
        wallet_address: str,
        limit: int,
    ) -> list[RawDataUserActivity]:
        response = await self._client.get(
            "/activity",
            params={
                "user": wallet_address,
                "limit": limit,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise TypeError(f"Expected list payload from Data API /activity, got {type(payload)!r}")

        fetched_at = utc_now()
        return [
            RawDataUserActivity(
                source="data_api.activity",
                fetched_at=fetched_at,
                wallet_address=wallet_address,
                payload=item,
            )
            for item in payload
            if isinstance(item, dict)
        ]

    async def aclose(self) -> None:
        await self._client.aclose()
