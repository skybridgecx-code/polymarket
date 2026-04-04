from __future__ import annotations

from typing import Any

from pydantic import BaseModel, RootModel


class HealthResponse(BaseModel):
    status: str


class OpportunityLegResponse(BaseModel):
    market_id: str
    question: str
    outcome: str
    token_id: str
    best_ask: str | None
    average_fill_price: str | None
    quantity: str | None
    fee_bps: int | None


class OpportunityResponse(BaseModel):
    event_slug: str
    opportunity_type: str
    legs: list[OpportunityLegResponse]
    gross_edge_cents: str | None
    estimated_fee_cents: str | None
    net_edge_cents: str | None
    capacity_shares_or_notional: str | None
    status: str
    rejection_reason: str | None
    explanation: str


class OpportunitiesResponse(RootModel[list[OpportunityResponse]]):
    pass


class WalletSeedResponse(BaseModel):
    source: str
    source_record_id: str
    source_reference: str
    discovered_at: str
    wallet_address: str
    seed_kind: str
    display_name: str | None
    pseudonym: str | None
    profile_image_url: str | None
    verified: bool | None
    leaderboard_rank: int | None
    leaderboard_volume: str | None
    leaderboard_pnl: str | None
    condition_id: str | None
    market_id: str | None
    market_slug: str | None
    event_slug: str | None
    token_id: str | None
    outcome: str | None
    outcome_index: int | None
    position_size: str | None


class WalletActivityResponse(BaseModel):
    source: str
    source_record_id: str
    source_reference: str
    fetched_at: str
    activity_at: str | None
    wallet_address: str
    activity_type: str
    transaction_hash: str | None
    condition_id: str | None
    market_slug: str | None
    event_slug: str | None
    title: str | None
    token_id: str | None
    side: str | None
    outcome: str | None
    outcome_index: int | None
    size: str | None
    usdc_size: str | None
    price: str | None


class WalletBackfillResponse(BaseModel):
    selected_wallets: list[str]
    wallet_seeds: list[WalletSeedResponse]
    wallet_activities: list[WalletActivityResponse]


class RelationshipEvidenceResponse(BaseModel):
    event_slug: str | None
    condition_id: str
    token_id: str
    side: str
    leader_activity_id: str
    follower_activity_id: str
    leader_activity_at: str
    follower_activity_at: str
    lag_seconds: int
    leader_source_reference: str
    follower_source_reference: str


class RelationshipResponse(BaseModel):
    leader_wallet: str
    follower_wallet: str
    relationship_type: str
    matched_events_count: int
    matched_legs_count: int
    lag_summary_seconds: dict[str, int | None]
    confidence_score: str | None
    status: str
    rejection_reason: str | None
    explanation: str
    evidence: list[RelationshipEvidenceResponse]


class RelationshipsResponse(RootModel[list[RelationshipResponse]]):
    pass


JSONValue = dict[str, Any] | list[Any] | str | int | float | bool | None
