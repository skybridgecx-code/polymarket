from __future__ import annotations

from polymarket_arb.models.normalized import (
    NormalizedBook,
    NormalizedEvent,
    NormalizedFeeRate,
    NormalizedWalletActivity,
    NormalizedWalletSeed,
)
from polymarket_arb.models.raw import (
    RawClobBook,
    RawClobFeeRate,
    RawDataLeaderboardEntry,
    RawDataUserActivity,
    RawGammaEvent,
)


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


def normalize_wallet_leaderboard_seeds(
    records: list[RawDataLeaderboardEntry],
) -> list[NormalizedWalletSeed]:
    seeds = [NormalizedWalletSeed.from_leaderboard_entry(record) for record in records]
    seeds.sort(key=lambda seed: (seed.leaderboard_rank or 10**9, seed.wallet_address))
    return seeds


def normalize_wallet_activities(
    records: list[RawDataUserActivity],
) -> list[NormalizedWalletActivity]:
    activities = [NormalizedWalletActivity.from_raw(record) for record in records]
    activities.sort(
        key=lambda activity: (
            activity.wallet_address,
            activity.activity_at or activity.fetched_at,
            activity.source_record_id,
        )
    )
    return activities
