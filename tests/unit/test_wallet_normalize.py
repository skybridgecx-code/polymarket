from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from polymarket_arb.ingest.normalize import (
    normalize_events,
    normalize_wallet_activities,
    normalize_wallet_leaderboard_seeds,
)
from polymarket_arb.models.normalized import NormalizedWalletSeed
from polymarket_arb.models.raw import (
    RawDataLeaderboardEntry,
    RawDataTopHolderGroup,
    RawDataUserActivity,
    RawGammaEvent,
)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_wallet_seed_normalization_preserves_source_and_market_references() -> None:
    fixture_path = Path("tests/fixtures/scenarios/phase3_wallet_backfill.json")
    payload = _load_json(fixture_path)
    assert isinstance(payload, dict)

    fetched_at = datetime(2026, 4, 4, tzinfo=UTC)
    leaderboard_records = [
        RawDataLeaderboardEntry(
            source="data_api.leaderboard",
            fetched_at=fetched_at,
            time_period="DAY",
            order_by="VOL",
            payload=item,
        )
        for item in payload["leaderboard"]
    ]
    leaderboard_seeds = normalize_wallet_leaderboard_seeds(leaderboard_records)

    assert leaderboard_seeds[0].wallet_address == "0xaaa0000000000000000000000000000000000001"
    assert leaderboard_seeds[0].source_record_id.startswith(
        "data_api.leaderboard:day:vol:1:"
    )
    assert leaderboard_seeds[0].leaderboard_rank == 1
    assert str(leaderboard_seeds[0].leaderboard_volume) == "1000.5"

    raw_events = [
        RawGammaEvent(source="gamma.events", fetched_at=fetched_at, payload=item)
        for item in payload["events"]
    ]
    events = normalize_events(raw_events)
    markets_by_token = {
        token_id: (event.slug, market)
        for event in events
        for market in event.markets
        for token_id in market.token_ids
    }

    holder_group = RawDataTopHolderGroup(
        source="data_api.holders",
        fetched_at=fetched_at,
        condition_ids=["0xcondition1"],
        payload=payload["holders"][0],
    )
    top_holder_seed = NormalizedWalletSeed.from_top_holder_group(
        record=holder_group,
        holder_payload=payload["holders"][0]["holders"][1],
        market=markets_by_token["token_yes_1"][1],
        event_slug=markets_by_token["token_yes_1"][0],
    )

    assert top_holder_seed.seed_kind == "top_holder"
    assert top_holder_seed.condition_id == "0xcondition1"
    assert top_holder_seed.market_slug == "fed-cut-september-2026"
    assert top_holder_seed.event_slug == "fed-cut-september-2026"
    assert top_holder_seed.outcome == "Yes"
    assert str(top_holder_seed.position_size) == "120.5"


def test_wallet_activity_normalization_keeps_missing_fields_explicit() -> None:
    fixture_path = Path("tests/fixtures/scenarios/phase3_wallet_backfill.json")
    payload = _load_json(fixture_path)
    assert isinstance(payload, dict)

    fetched_at = datetime(2026, 4, 4, tzinfo=UTC)
    activity_records = [
        RawDataUserActivity(
            source="data_api.activity",
            fetched_at=fetched_at,
            wallet_address=wallet_address,
            payload=item,
        )
        for wallet_address, items in payload["activities_by_wallet"].items()
        for item in items
    ]
    activities = normalize_wallet_activities(activity_records)

    assert len(activities) == 2
    assert activities[0].wallet_address == "0xaaa0000000000000000000000000000000000001"
    assert activities[0].activity_at == datetime.fromtimestamp(1710000000, tz=UTC)
    assert activities[0].transaction_hash == "0xtxaaa1"
    assert activities[0].token_id == "token_yes_1"

    merge_activity = activities[1]
    assert merge_activity.wallet_address == "0xbbb0000000000000000000000000000000000002"
    assert merge_activity.transaction_hash is None
    assert merge_activity.token_id is None
    assert merge_activity.side is None
    assert merge_activity.outcome is None
    assert merge_activity.source_record_id.startswith("data_api.activity:")
