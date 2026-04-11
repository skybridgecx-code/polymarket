"""Parser behavior tests for deterministic crypto adapter normalization."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.crypto_adapter.models import CryptoAdapterError
from future_system.crypto_adapter.parser import parse_crypto_market_snapshots

_FIXTURE_PATH = Path("tests/fixtures/future_system/crypto/market_snapshots.json")


def test_fixture_parses_into_normalized_market_states() -> None:
    payload = _load_fixture_payload()

    result = parse_crypto_market_snapshots(payload)

    assert result.exchange == "deribit"
    assert len(result.market_states) == 3
    assert result.skipped_records == 1
    assert [state.symbol for state in result.market_states] == [
        "BTC-USD",
        "ETH-USD",
        "BTC-PERP",
    ]


def test_mid_price_is_computed_deterministically_when_missing() -> None:
    payload = _load_fixture_payload()

    result = parse_crypto_market_snapshots(payload)
    btc_spot = result.market_states[0]
    btc_perp = result.market_states[2]

    assert btc_spot.mid_price == 70325.0
    assert btc_perp.mid_price == 70410.0


def test_malformed_records_increase_skipped_records() -> None:
    payload = _load_fixture_payload()

    result = parse_crypto_market_snapshots(payload)

    assert result.skipped_records == 1
    assert result.flags == ["skipped_invalid_records"]


def test_spot_and_perp_records_are_supported() -> None:
    payload = _load_fixture_payload()

    result = parse_crypto_market_snapshots(payload)

    assert {state.market_type for state in result.market_states} == {"spot", "perp"}


def test_parser_flags_are_deterministic() -> None:
    payload = _load_fixture_payload()

    first = parse_crypto_market_snapshots(payload)
    second = parse_crypto_market_snapshots(payload)

    assert first.model_dump() == second.model_dump()


def test_invalid_payload_shape_raises_adapter_error() -> None:
    with pytest.raises(CryptoAdapterError):
        parse_crypto_market_snapshots("not-a-payload")


def _load_fixture_payload() -> list[dict[str, object]]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

