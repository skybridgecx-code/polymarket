from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from polymarket_arb.models.raw import RawWsMarketMessage


def _parse_optional_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, int | float):
        return datetime.fromtimestamp(float(value), tz=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise TypeError(f"Unsupported datetime value: {value!r}")


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat().replace("+00:00", "Z")


class MarketStreamEvent(BaseModel):
    source: str
    received_at: datetime
    event_type: str
    asset_id: str | None
    market_id: str | None
    payload: dict[str, Any]

    @classmethod
    def from_raw(cls, record: RawWsMarketMessage) -> MarketStreamEvent:
        payload = record.payload
        return cls(
            source=record.source,
            received_at=record.received_at,
            event_type=str(payload.get("event_type") or payload.get("type") or "unknown"),
            asset_id=(
                str(payload.get("asset_id"))
                if payload.get("asset_id") is not None
                else (
                    str(payload.get("asset"))
                    if payload.get("asset") is not None
                    else None
                )
            ),
            market_id=(
                str(payload.get("market"))
                if payload.get("market") is not None
                else (
                    str(payload.get("market_id"))
                    if payload.get("market_id") is not None
                    else None
                )
            ),
            payload=payload,
        )


class OrchestrationCheckpoint(BaseModel):
    schema_version: int = 1
    checkpoint_written_at: datetime | None = None
    last_scan_refresh_at: datetime | None = None
    last_relationship_refresh_at: datetime | None = None
    last_websocket_connect_at: datetime | None = None
    last_websocket_event_at: datetime | None = None
    websocket_reconnect_count: int = 0
    websocket_disconnect_count: int = 0
    last_error: str | None = None
    subscribed_asset_ids: list[str] = Field(default_factory=list)
    last_refresh_limit: int | None = None
    last_relationship_limit: int | None = None
    stale_reasons: list[str] = Field(default_factory=list)

    @classmethod
    def from_file_payload(cls, payload: dict[str, Any]) -> OrchestrationCheckpoint:
        return cls(
            schema_version=int(payload.get("schema_version", 1)),
            checkpoint_written_at=_parse_optional_datetime(payload.get("checkpoint_written_at")),
            last_scan_refresh_at=_parse_optional_datetime(payload.get("last_scan_refresh_at")),
            last_relationship_refresh_at=_parse_optional_datetime(
                payload.get("last_relationship_refresh_at")
            ),
            last_websocket_connect_at=_parse_optional_datetime(
                payload.get("last_websocket_connect_at")
            ),
            last_websocket_event_at=_parse_optional_datetime(payload.get("last_websocket_event_at")),
            websocket_reconnect_count=int(payload.get("websocket_reconnect_count", 0)),
            websocket_disconnect_count=int(payload.get("websocket_disconnect_count", 0)),
            last_error=(
                str(payload.get("last_error"))
                if payload.get("last_error") is not None
                else None
            ),
            subscribed_asset_ids=[
                str(item) for item in payload.get("subscribed_asset_ids", []) if item is not None
            ],
            last_refresh_limit=(
                int(payload["last_refresh_limit"])
                if payload.get("last_refresh_limit") is not None
                else None
            ),
            last_relationship_limit=(
                int(payload["last_relationship_limit"])
                if payload.get("last_relationship_limit") is not None
                else None
            ),
            stale_reasons=[
                str(item) for item in payload.get("stale_reasons", []) if item is not None
            ],
        )

    def to_file_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "checkpoint_written_at": _isoformat(self.checkpoint_written_at),
            "last_scan_refresh_at": _isoformat(self.last_scan_refresh_at),
            "last_relationship_refresh_at": _isoformat(self.last_relationship_refresh_at),
            "last_websocket_connect_at": _isoformat(self.last_websocket_connect_at),
            "last_websocket_event_at": _isoformat(self.last_websocket_event_at),
            "websocket_reconnect_count": self.websocket_reconnect_count,
            "websocket_disconnect_count": self.websocket_disconnect_count,
            "last_error": self.last_error,
            "subscribed_asset_ids": self.subscribed_asset_ids,
            "last_refresh_limit": self.last_refresh_limit,
            "last_relationship_limit": self.last_relationship_limit,
            "stale_reasons": self.stale_reasons,
        }


class OrchestrationHealthStatus(BaseModel):
    status: str
    stale: bool
    stale_reasons: list[str]
    checkpoint_path: str
    last_scan_refresh_at: str | None
    last_relationship_refresh_at: str | None
    last_websocket_connect_at: str | None
    last_websocket_event_at: str | None
    websocket_reconnect_count: int
    websocket_disconnect_count: int
    subscribed_asset_ids_count: int
    last_error: str | None

    @classmethod
    def from_checkpoint(
        cls,
        *,
        checkpoint: OrchestrationCheckpoint,
        checkpoint_path: Path,
        stale_reasons: list[str],
    ) -> OrchestrationHealthStatus:
        status = "ok"
        if (
            checkpoint.last_scan_refresh_at is None
            and checkpoint.last_relationship_refresh_at is None
        ):
            status = "idle"
        elif stale_reasons:
            status = "stale"

        return cls(
            status=status,
            stale=bool(stale_reasons),
            stale_reasons=stale_reasons,
            checkpoint_path=str(checkpoint_path),
            last_scan_refresh_at=_isoformat(checkpoint.last_scan_refresh_at),
            last_relationship_refresh_at=_isoformat(checkpoint.last_relationship_refresh_at),
            last_websocket_connect_at=_isoformat(checkpoint.last_websocket_connect_at),
            last_websocket_event_at=_isoformat(checkpoint.last_websocket_event_at),
            websocket_reconnect_count=checkpoint.websocket_reconnect_count,
            websocket_disconnect_count=checkpoint.websocket_disconnect_count,
            subscribed_asset_ids_count=len(checkpoint.subscribed_asset_ids),
            last_error=checkpoint.last_error,
        )
