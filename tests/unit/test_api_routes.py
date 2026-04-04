from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient
from polymarket_arb.api.main import create_app


class _FakeScanService:
    async def build_scan_rows(self, *, limit: int) -> list[dict[str, Any]]:
        return [
            {
                "event_slug": "event-a",
                "opportunity_type": "binary_complement",
                "legs": [
                    {
                        "market_id": "m1",
                        "question": "Question",
                        "outcome": "Yes",
                        "token_id": "t1",
                        "best_ask": "0.45",
                        "average_fill_price": "0.45",
                        "quantity": "10",
                        "fee_bps": 100,
                    }
                ],
                "gross_edge_cents": "10",
                "estimated_fee_cents": "1.2",
                "net_edge_cents": "8.8",
                "capacity_shares_or_notional": str(limit),
                "status": "accepted",
                "rejection_reason": None,
                "explanation": "Accepted sample opportunity.",
            }
        ]


class _FakeWalletBackfillService:
    async def build_wallet_backfill(self, *, limit: int) -> dict[str, Any]:
        return {
            "selected_wallets": ["0xabc"],
            "wallet_seeds": [
                {
                    "source": "data_api.leaderboard",
                    "source_record_id": "seed-1",
                    "source_reference": "/v1/leaderboard",
                    "discovered_at": "2026-04-04T00:00:00Z",
                    "wallet_address": "0xabc",
                    "seed_kind": "leaderboard",
                    "display_name": "Desk",
                    "pseudonym": None,
                    "profile_image_url": None,
                    "verified": False,
                    "leaderboard_rank": 1,
                    "leaderboard_volume": "100",
                    "leaderboard_pnl": "10",
                    "condition_id": None,
                    "market_id": None,
                    "market_slug": None,
                    "event_slug": None,
                    "token_id": None,
                    "outcome": None,
                    "outcome_index": None,
                    "position_size": None,
                }
            ],
            "wallet_activities": [
                {
                    "source": "data_api.activity",
                    "source_record_id": "activity-1",
                    "source_reference": "/activity?user=0xabc",
                    "fetched_at": "2026-04-04T00:00:00Z",
                    "activity_at": "2026-04-04T00:01:00Z",
                    "wallet_address": "0xabc",
                    "activity_type": "TRADE",
                    "transaction_hash": "0xtx",
                    "condition_id": "cond-1",
                    "market_slug": "market-1",
                    "event_slug": "event-1",
                    "title": "Event 1",
                    "token_id": "token-1",
                    "side": "BUY",
                    "outcome": "Yes",
                    "outcome_index": 0,
                    "size": "5",
                    "usdc_size": "2.5",
                    "price": "0.5",
                }
            ],
            "echo_limit": limit,
        }


class _FakeCopierDetectionService:
    async def build_relationship_reports(self, *, limit: int) -> list[dict[str, Any]]:
        return [
            {
                "leader_wallet": "0xleader",
                "follower_wallet": "0xfollower",
                "relationship_type": "same_leg_same_side_lag",
                "matched_events_count": 2,
                "matched_legs_count": 3,
                "lag_summary_seconds": {"min": 10, "median": 20, "max": 30},
                "confidence_score": "0.75",
                "status": "accepted",
                "rejection_reason": None,
                "explanation": f"Accepted sample relationship for limit {limit}.",
                "evidence": [
                    {
                        "event_slug": "event-1",
                        "condition_id": "cond-1",
                        "token_id": "token-1",
                        "side": "BUY",
                        "leader_activity_id": "leader-1",
                        "follower_activity_id": "follower-1",
                        "leader_activity_at": "2026-04-04T00:00:00Z",
                        "follower_activity_at": "2026-04-04T00:00:20Z",
                        "lag_seconds": 20,
                        "leader_source_reference": "/activity?user=0xleader",
                        "follower_source_reference": "/activity?user=0xfollower",
                    }
                ],
            }
        ]


def _app() -> TestClient:
    app = create_app(
        scan_service_factory=lambda settings: cast(Any, _FakeScanService()),
        wallet_backfill_service_factory=lambda settings: cast(Any, _FakeWalletBackfillService()),
        copier_detection_service_factory=lambda settings: cast(Any, _FakeCopierDetectionService()),
    )
    return TestClient(app)


def test_health_route_returns_ok() -> None:
    client = _app()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_opportunities_route_uses_existing_service_output() -> None:
    client = _app()
    response = client.get("/opportunities", params={"limit": 7})

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["capacity_shares_or_notional"] == "7"
    assert payload[0]["status"] == "accepted"
    assert payload[0]["explanation"] == "Accepted sample opportunity."


def test_wallet_backfill_route_returns_visible_wallet_payload() -> None:
    client = _app()
    response = client.get("/wallets/backfill", params={"limit": 4})

    assert response.status_code == 200
    payload = response.json()
    assert payload["selected_wallets"] == ["0xabc"]
    assert payload["wallet_seeds"][0]["source_reference"] == "/v1/leaderboard"
    assert payload["wallet_activities"][0]["source_record_id"] == "activity-1"


def test_relationships_route_preserves_explanation_and_evidence() -> None:
    client = _app()
    response = client.get("/relationships/copiers", params={"limit": 6})

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["leader_wallet"] == "0xleader"
    assert payload[0]["confidence_score"] == "0.75"
    assert payload[0]["status"] == "accepted"
    assert "limit 6" in payload[0]["explanation"]
    assert payload[0]["evidence"][0]["leader_source_reference"] == "/activity?user=0xleader"
