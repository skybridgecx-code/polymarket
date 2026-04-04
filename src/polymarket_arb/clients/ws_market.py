from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from websockets import ConnectionClosed
from websockets.asyncio.client import connect

from polymarket_arb.config import Settings
from polymarket_arb.models.orchestration import MarketStreamEvent
from polymarket_arb.models.raw import RawWsMarketMessage
from polymarket_arb.utils.time import utc_now


class SupportsWebSocket(Protocol):
    async def send(self, message: str) -> None: ...

    async def recv(self) -> str: ...


WebSocketFactory = Callable[[str], Any]
EventHandler = Callable[[MarketStreamEvent], Awaitable[None]]


class MarketWebSocketClient:
    def __init__(
        self,
        settings: Settings,
        *,
        websocket_factory: WebSocketFactory | None = None,
        sleep_fn: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._settings = settings
        self._websocket_factory = websocket_factory or self._default_websocket_factory
        self._sleep_fn = sleep_fn

    async def consume(
        self,
        *,
        asset_ids: list[str],
        max_messages: int,
        reconnect_attempts: int,
        receive_timeout_seconds: float,
        on_event: EventHandler,
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[str], None] | None = None,
        on_reconnect: Callable[[int], None] | None = None,
    ) -> int:
        if not asset_ids or max_messages <= 0:
            return 0

        received_count = 0
        attempt = 0
        while True:
            if on_reconnect is not None and attempt > 0:
                on_reconnect(attempt)

            try:
                async with self._websocket_factory(str(self._settings.ws_market_url)) as websocket:
                    if on_connect is not None:
                        on_connect()
                    await self._subscribe(websocket=websocket, asset_ids=asset_ids)

                    while received_count < max_messages:
                        raw_message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=receive_timeout_seconds,
                        )
                        message = self._parse_message(raw_message)
                        if message is None:
                            continue
                        await on_event(message)
                        received_count += 1

                    return received_count
            except (
                TimeoutError,
                ConnectionClosed,
                ConnectionError,
                OSError,
                json.JSONDecodeError,
            ) as exc:
                if on_disconnect is not None:
                    on_disconnect(str(exc))
                if attempt >= reconnect_attempts:
                    return received_count
                attempt += 1
                await self._sleep_fn(0)

    async def _subscribe(self, *, websocket: SupportsWebSocket, asset_ids: list[str]) -> None:
        await websocket.send(
            json.dumps(
                {
                    "assets_ids": asset_ids,
                    "type": "market",
                },
                sort_keys=True,
            )
        )

    def _parse_message(self, raw_message: str) -> MarketStreamEvent | None:
        stripped = raw_message.strip()
        if stripped in {"PONG", "PING"}:
            return None

        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            return None

        raw_record = RawWsMarketMessage(
            source="ws.market",
            received_at=utc_now(),
            payload=payload,
        )
        return MarketStreamEvent.from_raw(raw_record)

    def _default_websocket_factory(self, url: str) -> Any:
        return connect(url)
