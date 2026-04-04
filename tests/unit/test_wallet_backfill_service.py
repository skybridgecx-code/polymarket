from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from polymarket_arb.config import Settings
from polymarket_arb.models.raw import (
    RawDataLeaderboardEntry,
    RawDataTopHolderGroup,
    RawDataUserActivity,
    RawGammaEvent,
)
from polymarket_arb.services.wallet_backfill_service import WalletBackfillService


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class _FakeGammaClient:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self._fetched_at = datetime(2026, 4, 4, tzinfo=UTC)

    async def list_events(
        self,
        *,
        limit: int,
        active: bool = True,
        closed: bool = False,
        archived: bool = False,
    ) -> list[RawGammaEvent]:  # noqa: ARG002
        return [
            RawGammaEvent(source="gamma.events", fetched_at=self._fetched_at, payload=item)
            for item in self._payload["events"]
        ]

    async def aclose(self) -> None:
        return None


class _FakeDataApiClient:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self._fetched_at = datetime(2026, 4, 4, tzinfo=UTC)

    async def get_leaderboard(
        self,
        *,
        limit: int,
        time_period: str = "DAY",
        order_by: str = "VOL",
    ) -> list[RawDataLeaderboardEntry]:
        return [
            RawDataLeaderboardEntry(
                source="data_api.leaderboard",
                fetched_at=self._fetched_at,
                time_period=time_period,
                order_by=order_by,
                payload=item,
            )
            for item in self._payload["leaderboard"][:limit]
        ]

    async def get_holders(
        self,
        *,
        condition_ids: list[str],
        limit: int,
    ) -> list[RawDataTopHolderGroup]:
        return [
            RawDataTopHolderGroup(
                source="data_api.holders",
                fetched_at=self._fetched_at,
                condition_ids=condition_ids,
                payload={
                    "token": item["token"],
                    "holders": item["holders"][:limit],
                },
            )
            for item in self._payload["holders"]
        ]

    async def get_user_activity(
        self,
        *,
        wallet_address: str,
        limit: int,
    ) -> list[RawDataUserActivity]:
        items = self._payload["activities_by_wallet"].get(wallet_address, [])
        return [
            RawDataUserActivity(
                source="data_api.activity",
                fetched_at=self._fetched_at,
                wallet_address=wallet_address,
                payload=item,
            )
            for item in items[:limit]
        ]

    async def aclose(self) -> None:
        return None


def test_wallet_backfill_service_discovers_and_backfills_deterministically() -> None:
    fixture_path = Path("tests/fixtures/scenarios/phase3_wallet_backfill.json")
    payload = _load_json(fixture_path)
    assert isinstance(payload, dict)
    typed_payload = cast(dict[str, Any], payload)

    service = WalletBackfillService(
        Settings(),
        gamma_client=cast(Any, _FakeGammaClient(typed_payload)),
        data_api_client=cast(Any, _FakeDataApiClient(typed_payload)),
    )

    result = asyncio.run(service.build_wallet_backfill(limit=3))

    assert result["selected_wallets"] == [
        "0xaaa0000000000000000000000000000000000001",
        "0xbbb0000000000000000000000000000000000002",
        "0xccc0000000000000000000000000000000000003",
    ]
    assert len(result["wallet_seeds"]) == 5
    assert len(result["wallet_activities"]) == 2

    first_seed = result["wallet_seeds"][0]
    assert first_seed["seed_kind"] == "leaderboard"
    assert first_seed["source"] == "data_api.leaderboard"

    top_holder_seed = next(
        seed for seed in result["wallet_seeds"] if seed["wallet_address"].endswith("0003")
    )
    assert top_holder_seed["seed_kind"] == "top_holder"
    assert top_holder_seed["condition_id"] == "0xcondition1"

    merge_activity = next(
        activity
        for activity in result["wallet_activities"]
        if activity["wallet_address"].endswith("0002")
    )
    assert merge_activity["transaction_hash"] is None
    assert merge_activity["condition_id"] == "0xcondition1"
