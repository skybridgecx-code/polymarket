"""Assembler behavior tests for deterministic theme-linked crypto evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from future_system.crypto_evidence.assembler import assemble_theme_crypto_evidence_packet
from future_system.crypto_evidence.models import CryptoEvidenceAssemblyError
from future_system.theme_graph.models import ThemeLinkPacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/crypto/theme_crypto_states.json")
_REFERENCE_TIME = datetime(2026, 2, 1, 12, 10, tzinfo=UTC)


def test_linked_crypto_states_are_selected_correctly() -> None:
    packet = _theme_packet(
        assets=[
            _asset(symbol="BTC", asset_type="spot", role="confirmation_proxy"),
            _asset(symbol="BTC-PERP", asset_type="perp", role="primary_proxy"),
            _asset(symbol="ETH", asset_type="spot", role="context_only"),
            _asset(symbol="AAPL", asset_type="equity", role="context_only"),
        ]
    )

    evidence = assemble_theme_crypto_evidence_packet(
        theme_packet=packet,
        crypto_states=_fixture_states(),
        reference_time=_REFERENCE_TIME,
    )

    assert [item.symbol for item in evidence.proxy_evidence] == ["BTC-USD", "BTC-PERP", "ETH-USD"]
    assert "SOL-USD" not in evidence.matched_symbols


def test_non_crypto_theme_assets_are_ignored() -> None:
    packet = _theme_packet(
        assets=[
            _asset(symbol="BTC", asset_type="spot", role="primary_proxy"),
            _asset(symbol="AAPL", asset_type="equity", role="context_only"),
        ]
    )

    evidence = assemble_theme_crypto_evidence_packet(
        theme_packet=packet,
        crypto_states=_fixture_states(),
        reference_time=_REFERENCE_TIME,
    )

    assert set(evidence.matched_symbols) == {"BTC-USD", "BTC-PERP"}
    assert evidence.coverage_score == 1.0


def test_no_matches_raises_crypto_evidence_assembly_error() -> None:
    packet = _theme_packet(assets=[_asset(symbol="XRP", asset_type="spot", role="primary_proxy")])

    with pytest.raises(CryptoEvidenceAssemblyError):
        assemble_theme_crypto_evidence_packet(
            theme_packet=packet,
            crypto_states=_fixture_states(),
            reference_time=_REFERENCE_TIME,
        )


def test_no_crypto_linked_assets_raises_crypto_evidence_assembly_error() -> None:
    packet = _theme_packet(
        assets=[_asset(symbol="AAPL", asset_type="equity", role="context_only")]
    )

    with pytest.raises(CryptoEvidenceAssemblyError):
        assemble_theme_crypto_evidence_packet(
            theme_packet=packet,
            crypto_states=_fixture_states(),
            reference_time=_REFERENCE_TIME,
        )


def test_primary_proxy_selection_is_deterministic() -> None:
    packet = _theme_packet(
        assets=[
            _asset(symbol="ETH", asset_type="spot", role="primary_proxy"),
            _asset(symbol="BTC-PERP", asset_type="perp", role="confirmation_proxy"),
        ]
    )

    first = assemble_theme_crypto_evidence_packet(
        theme_packet=packet,
        crypto_states=_fixture_states(),
        reference_time=_REFERENCE_TIME,
    )
    second = assemble_theme_crypto_evidence_packet(
        theme_packet=packet,
        crypto_states=_fixture_states(),
        reference_time=_REFERENCE_TIME,
    )

    assert first.model_dump() == second.model_dump()
    assert first.primary_symbol == "ETH-USD"


def test_coverage_score_is_deterministic() -> None:
    packet = _theme_packet(
        assets=[
            _asset(symbol="BTC", asset_type="spot", role="primary_proxy"),
            _asset(symbol="ETH", asset_type="spot", role="confirmation_proxy"),
            _asset(symbol="XRP", asset_type="spot", role="context_only"),
        ]
    )

    evidence = assemble_theme_crypto_evidence_packet(
        theme_packet=packet,
        crypto_states=_fixture_states(),
        reference_time=_REFERENCE_TIME,
    )

    assert evidence.coverage_score == 0.667


def test_stale_and_incomplete_coverage_flags_surface_correctly() -> None:
    packet = _theme_packet(
        assets=[
            _asset(symbol="BTC", asset_type="spot", role="primary_proxy"),
            _asset(symbol="ETH", asset_type="spot", role="confirmation_proxy"),
            _asset(symbol="XRP", asset_type="spot", role="context_only"),
        ]
    )

    evidence = assemble_theme_crypto_evidence_packet(
        theme_packet=packet,
        crypto_states=_fixture_states(),
        reference_time=_REFERENCE_TIME,
    )

    assert "stale_snapshot" in evidence.flags
    assert "incomplete_linked_symbol_coverage" in evidence.flags


def test_explanation_string_is_deterministic() -> None:
    packet = _theme_packet(assets=[_asset(symbol="BTC", asset_type="spot", role="primary_proxy")])

    evidence = assemble_theme_crypto_evidence_packet(
        theme_packet=packet,
        crypto_states=_fixture_states(),
        reference_time=_REFERENCE_TIME,
    )

    assert evidence.explanation == (
        "Matched proxies=2 linked_symbols=1; "
        "primary_symbol=BTC-PERP; "
        "liquidity_score=0.949; "
        "freshness_score=1.000; "
        "coverage_score=1.000; "
        "flags=none."
    )


def _fixture_states() -> list[dict[str, object]]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _theme_packet(*, assets: list[dict[str, object]]) -> ThemeLinkPacket:
    return ThemeLinkPacket.model_validate(
        {
            "theme_id": "theme_crypto_test",
            "matched_polymarket_markets": [],
            "matched_assets": assets,
            "matched_entities": [],
            "ambiguity_flags": [],
            "confidence_score": 0.9,
            "explanation": "Fixture theme link packet for crypto evidence assembly tests.",
        }
    )


def _asset(
    *,
    symbol: str,
    asset_type: str,
    role: str,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "asset_type": asset_type,
        "relevance": 0.8,
        "role": role,
        "direction_if_theme_up": "up",
        "link_basis": "manual",
    }
