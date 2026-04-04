from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from polymarket_arb.clients.data_api import DataApiClient
from polymarket_arb.clients.gamma import GammaClient
from polymarket_arb.config import Settings
from polymarket_arb.ingest.normalize import (
    normalize_events,
    normalize_wallet_activities,
    normalize_wallet_leaderboard_seeds,
)
from polymarket_arb.models.normalized import (
    NormalizedEvent,
    NormalizedMarket,
    NormalizedWalletActivity,
    NormalizedWalletSeed,
)
from polymarket_arb.models.raw import RawDataTopHolderGroup

_TOP_HOLDER_MARKET_COUNT = 5
_TOP_HOLDER_LIMIT_PER_TOKEN = 3


class WalletBackfillService:
    def __init__(
        self,
        settings: Settings,
        *,
        gamma_client: GammaClient | None = None,
        data_api_client: DataApiClient | None = None,
    ) -> None:
        self._settings = settings
        self._gamma_client = gamma_client
        self._data_api_client = data_api_client

    async def collect_wallet_backfill(
        self,
        *,
        limit: int,
    ) -> tuple[list[str], list[NormalizedWalletSeed], list[NormalizedWalletActivity]]:
        gamma_client = self._gamma_client or GammaClient(self._settings)
        data_api_client = self._data_api_client or DataApiClient(self._settings)
        owns_gamma_client = self._gamma_client is None
        owns_data_api_client = self._data_api_client is None

        try:
            wallet_seeds = await self.discover_wallet_seeds(
                limit=limit,
                gamma_client=gamma_client,
                data_api_client=data_api_client,
            )
            selected_wallets = self.select_wallets_for_backfill(wallet_seeds, limit=limit)
            wallet_activities = await self.fetch_wallet_activity(
                wallet_addresses=selected_wallets,
                limit=limit,
                data_api_client=data_api_client,
            )
            return selected_wallets, wallet_seeds, wallet_activities
        finally:
            if owns_gamma_client:
                await gamma_client.aclose()
            if owns_data_api_client:
                await data_api_client.aclose()

    async def build_wallet_backfill(self, *, limit: int) -> dict[str, Any]:
        selected_wallets, wallet_seeds, wallet_activities = await self.collect_wallet_backfill(
            limit=limit
        )
        return {
            "selected_wallets": selected_wallets,
            "wallet_seeds": [seed.model_dump(mode="json") for seed in wallet_seeds],
            "wallet_activities": [
                activity.model_dump(mode="json") for activity in wallet_activities
            ],
        }

    async def discover_wallet_seeds(
        self,
        *,
        limit: int,
        gamma_client: GammaClient,
        data_api_client: DataApiClient,
    ) -> list[NormalizedWalletSeed]:
        leaderboard_seeds = await self.discover_leaderboard_seeds(
            limit=limit,
            data_api_client=data_api_client,
        )
        top_holder_seeds = await self.discover_top_holder_seeds(
            limit=limit,
            gamma_client=gamma_client,
            data_api_client=data_api_client,
        )
        seeds = leaderboard_seeds + top_holder_seeds
        seeds.sort(key=self._seed_sort_key)
        return seeds

    async def discover_leaderboard_seeds(
        self,
        *,
        limit: int,
        data_api_client: DataApiClient,
    ) -> list[NormalizedWalletSeed]:
        raw_entries = await data_api_client.get_leaderboard(limit=limit)
        return normalize_wallet_leaderboard_seeds(raw_entries)

    async def discover_top_holder_seeds(
        self,
        *,
        limit: int,
        gamma_client: GammaClient,
        data_api_client: DataApiClient,
    ) -> list[NormalizedWalletSeed]:
        raw_events = await gamma_client.list_events(limit=max(limit * 3, 25))
        events = normalize_events(raw_events)
        markets_by_token = self._markets_by_token(events)
        selected_markets = self._top_holder_markets(events, limit=limit)

        condition_ids = [
            market.condition_id
            for market in selected_markets
            if market.condition_id is not None
        ]
        if not condition_ids:
            return []

        raw_groups = await data_api_client.get_holders(
            condition_ids=condition_ids,
            limit=min(limit, _TOP_HOLDER_LIMIT_PER_TOKEN),
        )
        seeds = self._normalize_top_holder_groups(
            raw_groups=raw_groups,
            markets_by_token=markets_by_token,
        )
        seeds.sort(key=self._seed_sort_key)
        return seeds

    async def fetch_wallet_activity(
        self,
        *,
        wallet_addresses: list[str],
        limit: int,
        data_api_client: DataApiClient,
    ) -> list[NormalizedWalletActivity]:
        results = await asyncio.gather(
            *(
                data_api_client.get_user_activity(wallet_address=wallet_address, limit=limit)
                for wallet_address in wallet_addresses
            ),
            return_exceptions=True,
        )

        raw_activities = []
        for result in results:
            if isinstance(result, list):
                raw_activities.extend(result)

        return normalize_wallet_activities(raw_activities)

    def select_wallets_for_backfill(
        self,
        wallet_seeds: list[NormalizedWalletSeed],
        *,
        limit: int,
    ) -> list[str]:
        selected_wallets: list[str] = []
        seen_wallets: set[str] = set()

        for seed in sorted(wallet_seeds, key=self._seed_sort_key):
            if seed.wallet_address in seen_wallets:
                continue
            seen_wallets.add(seed.wallet_address)
            selected_wallets.append(seed.wallet_address)
            if len(selected_wallets) >= limit:
                break

        return selected_wallets

    def _normalize_top_holder_groups(
        self,
        *,
        raw_groups: list[RawDataTopHolderGroup],
        markets_by_token: dict[str, tuple[str | None, NormalizedMarket]],
    ) -> list[NormalizedWalletSeed]:
        seeds: list[NormalizedWalletSeed] = []

        for group in raw_groups:
            token_id = str(group.payload.get("token") or "")
            if not token_id:
                continue

            event_slug: str | None = None
            market: NormalizedMarket | None = None
            if token_id in markets_by_token:
                event_slug, market = markets_by_token[token_id]

            holders = group.payload.get("holders", [])
            if not isinstance(holders, list):
                continue

            for holder in holders:
                if not isinstance(holder, dict):
                    continue
                seeds.append(
                    NormalizedWalletSeed.from_top_holder_group(
                        record=group,
                        holder_payload=holder,
                        market=market,
                        event_slug=event_slug,
                    )
                )

        return seeds

    def _markets_by_token(
        self,
        events: list[NormalizedEvent],
    ) -> dict[str, tuple[str | None, NormalizedMarket]]:
        indexed: dict[str, tuple[str | None, NormalizedMarket]] = {}
        for event in events:
            for market in event.markets:
                for token_id in market.token_ids:
                    indexed[token_id] = (event.slug, market)
        return indexed

    def _top_holder_markets(
        self,
        events: list[NormalizedEvent],
        *,
        limit: int,
    ) -> list[NormalizedMarket]:
        ordered_markets = [
            market
            for event in events
            for market in event.markets
            if market.condition_id is not None
        ]
        ordered_markets.sort(key=lambda market: (market.slug, market.market_id))
        return ordered_markets[: min(max(limit, 1), _TOP_HOLDER_MARKET_COUNT)]

    def _seed_sort_key(self, seed: NormalizedWalletSeed) -> tuple[object, ...]:
        seed_kind_rank = 0 if seed.seed_kind == "leaderboard" else 1
        leaderboard_rank = seed.leaderboard_rank if seed.leaderboard_rank is not None else 10**9
        position_size = seed.position_size if seed.position_size is not None else Decimal("-1")
        return (
            seed_kind_rank,
            leaderboard_rank,
            -position_size,
            seed.event_slug or "",
            seed.market_id or "",
            seed.token_id or "",
            seed.wallet_address,
            seed.source_record_id,
        )
