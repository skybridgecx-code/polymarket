from __future__ import annotations

from pathlib import Path

import pytest
from polymarket_arb.config import Settings


def test_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("POLY_GAMMA_BASE_URL", "https://gamma-api.polymarket.com")
    monkeypatch.setenv("POLY_CLOB_BASE_URL", "https://clob.polymarket.com")
    monkeypatch.setenv("POLY_DATA_BASE_URL", "https://data-api.polymarket.com")
    monkeypatch.setenv("POLY_WS_MARKET_URL", "wss://ws-subscriptions-clob.polymarket.com/ws/market")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()
    settings.ensure_directories()

    assert str(settings.gamma_base_url) == "https://gamma-api.polymarket.com/"
    assert settings.data_dir == tmp_path / "data"
    assert settings.state_dir == tmp_path / "state"
    assert settings.log_level == "DEBUG"
    assert settings.data_dir.exists()
    assert settings.state_dir.exists()
