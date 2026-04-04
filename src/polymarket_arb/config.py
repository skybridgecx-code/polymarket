from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import cast

from pydantic import AnyHttpUrl, AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gamma_base_url: AnyHttpUrl = Field(
        default=cast(AnyHttpUrl, "https://gamma-api.polymarket.com"),
        validation_alias="POLY_GAMMA_BASE_URL",
    )
    clob_base_url: AnyHttpUrl = Field(
        default=cast(AnyHttpUrl, "https://clob.polymarket.com"),
        validation_alias="POLY_CLOB_BASE_URL",
    )
    data_base_url: AnyHttpUrl = Field(
        default=cast(AnyHttpUrl, "https://data-api.polymarket.com"),
        validation_alias="POLY_DATA_BASE_URL",
    )
    ws_market_url: AnyUrl = Field(
        default=cast(AnyUrl, "wss://ws-subscriptions-clob.polymarket.com/ws/market"),
        validation_alias="POLY_WS_MARKET_URL",
    )
    data_dir: Path = Field(default=Path("./data"), validation_alias="DATA_DIR")
    state_dir: Path = Field(default=Path("./state"), validation_alias="STATE_DIR")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    request_timeout_seconds: float = 10.0
    scan_stale_after_seconds: int = 300
    relationship_stale_after_seconds: int = 300
    websocket_stale_after_seconds: int = 120
    websocket_receive_timeout_seconds: float = 2.0
    websocket_reconnect_attempts: int = 2
    orchestration_checkpoint_file: str = "runtime_orchestrator_checkpoint.json"
    paper_trade_min_size: Decimal = Decimal("5")
    paper_trade_max_size: Decimal = Decimal("10")
    paper_trade_max_capacity_utilization: Decimal = Decimal("0.5")
    paper_trade_min_simulated_edge_cents: Decimal = Decimal("5")
    paper_trade_base_slippage_bps: int = 10
    paper_trade_additional_leg_slippage_bps: int = 5
    paper_trade_utilization_slippage_bps: int = 20

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
