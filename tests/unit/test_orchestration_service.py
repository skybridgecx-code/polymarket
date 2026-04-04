from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from polymarket_arb.config import Settings
from polymarket_arb.models.orchestration import MarketStreamEvent, OrchestrationCheckpoint
from polymarket_arb.services.orchestration_service import RefreshOrchestratorService


class _FakeScanService:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    async def build_scan_rows(self, *, limit: int) -> list[dict[str, Any]]:
        return self._rows[:limit]


class _FakeCopierDetectionService:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    async def build_relationship_reports(self, *, limit: int) -> list[dict[str, Any]]:
        return self._rows[:limit]


class _FakeWsClient:
    def __init__(self, scripts: list[list[object]]) -> None:
        self._scripts = scripts
        self.calls: list[list[str]] = []

    async def consume(
        self,
        *,
        asset_ids: list[str],
        max_messages: int,
        reconnect_attempts: int,
        receive_timeout_seconds: float,
        on_event,
        on_connect,
        on_disconnect,
        on_reconnect,
    ) -> int:
        del reconnect_attempts, receive_timeout_seconds
        self.calls.append(asset_ids)
        received = 0

        for attempt, script in enumerate(self._scripts):
            if attempt > 0:
                on_reconnect(attempt)
            on_connect()
            for item in script:
                if isinstance(item, Exception):
                    on_disconnect(str(item))
                    break
                await on_event(item)
                received += 1
                if received >= max_messages:
                    return received
        return received


def _settings(tmp_path: Path) -> Settings:
    settings = Settings(
        DATA_DIR=tmp_path / "data",
        STATE_DIR=tmp_path / "state",
        POLY_GAMMA_BASE_URL="https://gamma-api.polymarket.com",
        POLY_CLOB_BASE_URL="https://clob.polymarket.com",
        POLY_DATA_BASE_URL="https://data-api.polymarket.com",
        POLY_WS_MARKET_URL="wss://ws-subscriptions-clob.polymarket.com/ws/market",
    )
    settings.ensure_directories()
    settings.scan_stale_after_seconds = 60
    settings.relationship_stale_after_seconds = 60
    settings.websocket_stale_after_seconds = 60
    settings.websocket_reconnect_attempts = 2
    return settings


def _event(asset_id: str) -> MarketStreamEvent:
    return MarketStreamEvent(
        source="ws.market",
        received_at=datetime(2026, 4, 4, tzinfo=UTC),
        event_type="book",
        asset_id=asset_id,
        market_id=None,
        payload={"asset_id": asset_id, "event_type": "book"},
    )


def test_orchestration_service_reconnects_and_writes_checkpoint(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ws_client = _FakeWsClient(
        scripts=[
            [ConnectionError("first disconnect")],
            [_event("token-a")],
        ]
    )
    service = RefreshOrchestratorService(
        settings,
        scan_service=_FakeScanService(
            [
                {
                    "event_slug": "event-a",
                    "opportunity_type": "binary_complement",
                    "legs": [{"token_id": "token-a"}],
                    "gross_edge_cents": "0",
                    "estimated_fee_cents": "0",
                    "net_edge_cents": "0",
                    "capacity_shares_or_notional": "0",
                    "status": "rejected",
                    "rejection_reason": "no_gross_edge",
                    "explanation": "sample",
                }
            ]
        ),
        copier_detection_service=_FakeCopierDetectionService([]),
        ws_client=ws_client,  # type: ignore[arg-type]
    )

    result = asyncio.run(
        service.run_refresh_cycle(
            scan_limit=5,
            relationship_limit=10,
            max_websocket_messages=1,
        )
    )

    assert result["checkpoint"]["websocket_reconnect_count"] == 1
    assert result["checkpoint"]["websocket_disconnect_count"] == 1
    assert result["checkpoint"]["subscribed_asset_ids"] == ["token-a"]

    checkpoint_path = settings.state_dir / settings.orchestration_checkpoint_file
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert payload["subscribed_asset_ids"] == ["token-a"]
    assert payload["last_websocket_event_at"] is not None


def test_orchestration_service_marks_stale_state_from_old_checkpoint(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    checkpoint = OrchestrationCheckpoint.from_file_payload(
        {
            "last_scan_refresh_at": "2026-04-04T00:00:00Z",
            "last_relationship_refresh_at": "2026-04-04T00:00:00Z",
            "last_websocket_event_at": "2026-04-04T00:00:00Z",
            "subscribed_asset_ids": ["token-a"],
        }
    )
    checkpoint_path = settings.state_dir / settings.orchestration_checkpoint_file
    checkpoint_path.write_text(
        json.dumps(checkpoint.to_file_payload(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    service = RefreshOrchestratorService(
        settings,
        scan_service=_FakeScanService([]),
        copier_detection_service=_FakeCopierDetectionService([]),
        ws_client=_FakeWsClient([]),  # type: ignore[arg-type]
    )

    health = service.build_health_status()

    assert health.status == "stale"
    assert "scan_refresh_overdue" in health.stale_reasons
    assert "relationship_refresh_overdue" in health.stale_reasons
    assert "websocket_event_overdue" in health.stale_reasons


def test_orchestration_service_resumes_subscription_from_checkpoint(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    checkpoint = OrchestrationCheckpoint(subscribed_asset_ids=["resume-token"])
    checkpoint_path = settings.state_dir / settings.orchestration_checkpoint_file
    checkpoint_path.write_text(
        json.dumps(checkpoint.to_file_payload(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    ws_client = _FakeWsClient([[]])
    service = RefreshOrchestratorService(
        settings,
        scan_service=_FakeScanService([]),
        copier_detection_service=_FakeCopierDetectionService([]),
        ws_client=ws_client,  # type: ignore[arg-type]
    )

    asyncio.run(
        service.run_refresh_cycle(
            scan_limit=5,
            relationship_limit=10,
            max_websocket_messages=0,
        )
    )

    assert ws_client.calls == []

    asyncio.run(
        service.run_refresh_cycle(
            scan_limit=5,
            relationship_limit=10,
            max_websocket_messages=1,
        )
    )

    assert ws_client.calls[0] == ["resume-token"]
