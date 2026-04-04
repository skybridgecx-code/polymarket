from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from polymarket_arb.clients.ws_market import MarketWebSocketClient
from polymarket_arb.config import Settings
from polymarket_arb.models.orchestration import (
    MarketStreamEvent,
    OrchestrationCheckpoint,
    OrchestrationHealthStatus,
)
from polymarket_arb.services.copier_detection_service import CopierDetectionService
from polymarket_arb.services.scan_service import ScanService
from polymarket_arb.utils.time import utc_now


class RefreshOrchestratorService:
    def __init__(
        self,
        settings: Settings,
        *,
        scan_service: ScanService | None = None,
        copier_detection_service: CopierDetectionService | None = None,
        ws_client: MarketWebSocketClient | None = None,
    ) -> None:
        self._settings = settings
        self._scan_service = scan_service or ScanService(settings)
        self._copier_detection_service = (
            copier_detection_service or CopierDetectionService(settings)
        )
        self._ws_client = ws_client or MarketWebSocketClient(settings)

    async def run_refresh_cycle(
        self,
        *,
        scan_limit: int,
        relationship_limit: int,
        max_websocket_messages: int,
    ) -> dict[str, Any]:
        checkpoint = self.load_checkpoint()

        scan_rows = await self._scan_service.build_scan_rows(limit=scan_limit)
        checkpoint.last_scan_refresh_at = utc_now()
        checkpoint.last_refresh_limit = scan_limit
        checkpoint.last_error = None

        relationship_rows = await self._copier_detection_service.build_relationship_reports(
            limit=relationship_limit
        )
        checkpoint.last_relationship_refresh_at = utc_now()
        checkpoint.last_relationship_limit = relationship_limit

        asset_ids = self._subscription_asset_ids(scan_rows=scan_rows, checkpoint=checkpoint)
        checkpoint.subscribed_asset_ids = asset_ids

        await self._consume_market_events(
            checkpoint=checkpoint,
            asset_ids=asset_ids,
            max_websocket_messages=max_websocket_messages,
        )

        stale_reasons = self._stale_reasons(checkpoint=checkpoint, now=utc_now())
        checkpoint.stale_reasons = stale_reasons
        checkpoint.checkpoint_written_at = utc_now()
        self.write_checkpoint(checkpoint)

        return {
            "scan_limit": scan_limit,
            "relationship_limit": relationship_limit,
            "max_websocket_messages": max_websocket_messages,
            "consumed_asset_ids": asset_ids,
            "checkpoint": checkpoint.to_file_payload(),
            "health": self.build_health_status().model_dump(mode="json"),
            "opportunities_count": len(scan_rows),
            "relationships_count": len(relationship_rows),
        }

    def build_health_status(self) -> OrchestrationHealthStatus:
        checkpoint = self.load_checkpoint()
        stale_reasons = self._stale_reasons(checkpoint=checkpoint, now=utc_now())
        return OrchestrationHealthStatus.from_checkpoint(
            checkpoint=checkpoint,
            checkpoint_path=self._checkpoint_path(),
            stale_reasons=stale_reasons,
        )

    def load_checkpoint(self) -> OrchestrationCheckpoint:
        checkpoint_path = self._checkpoint_path()
        if not checkpoint_path.exists():
            return OrchestrationCheckpoint()

        payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("Orchestration checkpoint file must contain a JSON object.")
        return OrchestrationCheckpoint.from_file_payload(payload)

    def write_checkpoint(self, checkpoint: OrchestrationCheckpoint) -> None:
        checkpoint_path = self._checkpoint_path()
        checkpoint_path.write_text(
            json.dumps(checkpoint.to_file_payload(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    async def _consume_market_events(
        self,
        *,
        checkpoint: OrchestrationCheckpoint,
        asset_ids: list[str],
        max_websocket_messages: int,
    ) -> None:
        if not asset_ids or max_websocket_messages <= 0:
            return

        checkpoint.last_websocket_connect_at = utc_now()
        messages_consumed = await self._ws_client.consume(
            asset_ids=asset_ids,
            max_messages=max_websocket_messages,
            reconnect_attempts=self._settings.websocket_reconnect_attempts,
            receive_timeout_seconds=self._settings.websocket_receive_timeout_seconds,
            on_event=lambda event: self._handle_market_event(checkpoint=checkpoint, event=event),
            on_connect=lambda: None,
            on_disconnect=lambda error: self._record_disconnect(checkpoint=checkpoint, error=error),
            on_reconnect=lambda attempt: self._record_reconnect(
                checkpoint=checkpoint,
                attempt=attempt,
            ),
        )

        if max_websocket_messages > 0 and messages_consumed == 0 and asset_ids:
            checkpoint.last_error = (
                "websocket_consumer_exited_without_messages"
                if checkpoint.last_error is None
                else checkpoint.last_error
            )

    async def _handle_market_event(
        self,
        *,
        checkpoint: OrchestrationCheckpoint,
        event: MarketStreamEvent,
    ) -> None:
        checkpoint.last_websocket_event_at = event.received_at
        checkpoint.last_error = None

    def _record_disconnect(self, *, checkpoint: OrchestrationCheckpoint, error: str) -> None:
        checkpoint.websocket_disconnect_count += 1
        checkpoint.last_error = error

    def _record_reconnect(
        self,
        *,
        checkpoint: OrchestrationCheckpoint,
        attempt: int,
    ) -> None:
        checkpoint.websocket_reconnect_count = max(checkpoint.websocket_reconnect_count, attempt)
        checkpoint.last_websocket_connect_at = utc_now()

    def _subscription_asset_ids(
        self,
        *,
        scan_rows: list[dict[str, Any]],
        checkpoint: OrchestrationCheckpoint,
    ) -> list[str]:
        asset_ids = sorted(
            {
                str(leg["token_id"])
                for row in scan_rows
                for leg in row.get("legs", [])
                if leg.get("token_id")
            }
        )
        if asset_ids:
            return asset_ids
        return checkpoint.subscribed_asset_ids

    def _stale_reasons(
        self,
        *,
        checkpoint: OrchestrationCheckpoint,
        now: datetime,
    ) -> list[str]:
        reasons: list[str] = []

        if checkpoint.last_scan_refresh_at is None:
            reasons.append("scan_never_refreshed")
        elif (
            now - checkpoint.last_scan_refresh_at
        ).total_seconds() > self._settings.scan_stale_after_seconds:
            reasons.append("scan_refresh_overdue")

        if checkpoint.last_relationship_refresh_at is None:
            reasons.append("relationships_never_refreshed")
        elif (
            now - checkpoint.last_relationship_refresh_at
        ).total_seconds() > self._settings.relationship_stale_after_seconds:
            reasons.append("relationship_refresh_overdue")

        if checkpoint.subscribed_asset_ids:
            if checkpoint.last_websocket_event_at is None:
                reasons.append("websocket_never_received_event")
            elif (
                now - checkpoint.last_websocket_event_at
            ).total_seconds() > self._settings.websocket_stale_after_seconds:
                reasons.append("websocket_event_overdue")

        if checkpoint.last_error is not None:
            reasons.append("last_error_present")

        return reasons

    def _checkpoint_path(self) -> Path:
        return self._settings.state_dir / self._settings.orchestration_checkpoint_file
