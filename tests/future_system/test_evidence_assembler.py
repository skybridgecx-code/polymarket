"""Assembler behavior tests for deterministic future_system evidence packets."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from future_system.evidence.assembler import assemble_theme_evidence_packet
from future_system.evidence.models import EvidenceAssemblyError
from future_system.theme_graph.models import ThemeLinkPacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/evidence/polymarket_market_states.json")
_REFERENCE_TIME = datetime(2026, 1, 10, 12, 10, tzinfo=UTC)


def test_linked_market_is_matched_by_condition_id() -> None:
    packet = _theme_packet(
        [
            _link(condition_id="0xlinkedprimary"),
            _link(market_slug="fed-cut-june-2026-secondary"),
        ]
    )

    evidence = assemble_theme_evidence_packet(
        theme_packet=packet,
        market_states=_market_states_fixture(),
        reference_time=_REFERENCE_TIME,
    )

    matched_condition_ids = {item.condition_id for item in evidence.market_evidence}
    assert "0xlinkedprimary" in matched_condition_ids


def test_linked_market_is_matched_by_market_slug() -> None:
    packet = _theme_packet([_link(market_slug="fed-cut-june-2026-secondary")])

    evidence = assemble_theme_evidence_packet(
        theme_packet=packet,
        market_states=_market_states_fixture(),
        reference_time=_REFERENCE_TIME,
    )

    slugs = {item.market_slug for item in evidence.market_evidence}
    assert "fed-cut-june-2026-secondary" in slugs


def test_unlinked_markets_are_excluded() -> None:
    packet = _theme_packet([_link(condition_id="0xlinkedprimary")])

    evidence = assemble_theme_evidence_packet(
        theme_packet=packet,
        market_states=_market_states_fixture(),
        reference_time=_REFERENCE_TIME,
    )

    slugs = {item.market_slug for item in evidence.market_evidence}
    assert "unrelated-weather-market" not in slugs


def test_no_matches_raise_evidence_assembly_error() -> None:
    packet = _theme_packet([_link(condition_id="0xnotfound")])

    with pytest.raises(EvidenceAssemblyError):
        assemble_theme_evidence_packet(
            theme_packet=packet,
            market_states=_market_states_fixture(),
            reference_time=_REFERENCE_TIME,
        )


def test_primary_market_selection_is_deterministic() -> None:
    packet = _theme_packet(
        [
            _link(condition_id="0xprimary-low-liquidity"),
            _link(market_slug="high-liquidity-fallback"),
        ]
    )
    custom_states = [
        {
            "market_slug": "primary-condition-market",
            "event_slug": "event-a",
            "condition_id": "0xprimary-low-liquidity",
            "question": "Condition-linked market",
            "yes_bid": 0.45,
            "yes_ask": 0.65,
            "no_bid": 0.35,
            "no_ask": 0.55,
            "last_price_yes": 0.5,
            "volume_24h": 1200.0,
            "depth_near_mid": 60.0,
            "snapshot_at": "2026-01-10T12:09:00Z",
            "last_trade_at": "2026-01-10T12:08:00Z",
            "resolution_at": "2026-06-30T12:00:00Z",
            "status": "active",
        },
        {
            "market_slug": "high-liquidity-fallback",
            "event_slug": "event-b",
            "condition_id": "0xdifferent",
            "question": "Slug-linked fallback market",
            "yes_bid": 0.55,
            "yes_ask": 0.56,
            "no_bid": 0.44,
            "no_ask": 0.45,
            "last_price_yes": 0.555,
            "volume_24h": 500000.0,
            "depth_near_mid": 20000.0,
            "snapshot_at": "2026-01-10T12:09:30Z",
            "last_trade_at": "2026-01-10T12:09:00Z",
            "resolution_at": "2026-06-30T12:00:00Z",
            "status": "active",
        },
    ]

    packet_a = assemble_theme_evidence_packet(
        theme_packet=packet,
        market_states=custom_states,
        reference_time=_REFERENCE_TIME,
    )
    packet_b = assemble_theme_evidence_packet(
        theme_packet=packet,
        market_states=custom_states,
        reference_time=_REFERENCE_TIME,
    )

    assert packet_a.model_dump() == packet_b.model_dump()
    assert packet_a.primary_market_slug == "primary-condition-market"


def test_aggregate_probability_calculation_is_deterministic() -> None:
    packet = _theme_packet(
        [
            _link(condition_id="0xlinkedprimary"),
            _link(market_slug="fed-cut-june-2026-secondary"),
        ]
    )

    evidence_a = assemble_theme_evidence_packet(
        theme_packet=packet,
        market_states=_market_states_fixture(),
        reference_time=_REFERENCE_TIME,
    )
    evidence_b = assemble_theme_evidence_packet(
        theme_packet=packet,
        market_states=_market_states_fixture(),
        reference_time=_REFERENCE_TIME,
    )

    assert evidence_a.aggregate_yes_probability == evidence_b.aggregate_yes_probability
    assert evidence_a.aggregate_yes_probability == pytest.approx(0.570081, abs=1e-6)


def test_stale_flag_is_emitted_when_snapshot_is_old() -> None:
    packet = _theme_packet([_link(event_slug="fed-rate-cut-june-2026")])

    evidence = assemble_theme_evidence_packet(
        theme_packet=packet,
        market_states=_market_states_fixture(),
        reference_time=_REFERENCE_TIME,
    )

    assert "stale_snapshot" in evidence.flags
    stale_markets = [
        item.market_slug for item in evidence.market_evidence if "stale_snapshot" in item.flags
    ]
    assert stale_markets == ["fed-cut-june-2026-secondary"]


def test_missing_book_data_flag_is_emitted_when_bid_ask_missing() -> None:
    packet = _theme_packet([_link(market_slug="bookless-linked-market")])
    market_states = [
        {
            "market_slug": "bookless-linked-market",
            "event_slug": "bookless-event",
            "condition_id": "0xbookless",
            "question": "Missing bid/ask should emit explicit flag.",
            "yes_bid": None,
            "yes_ask": None,
            "no_bid": 0.49,
            "no_ask": 0.51,
            "last_price_yes": 0.5,
            "volume_24h": 9000.0,
            "depth_near_mid": 500.0,
            "snapshot_at": "2026-01-10T12:09:00Z",
            "last_trade_at": "2026-01-10T12:08:00Z",
            "resolution_at": "2026-06-30T12:00:00Z",
            "status": "active",
        }
    ]

    evidence = assemble_theme_evidence_packet(
        theme_packet=packet,
        market_states=market_states,
        reference_time=_REFERENCE_TIME,
    )

    assert "missing_book_data" in evidence.flags
    assert "missing_book_data" in evidence.market_evidence[0].flags


def _market_states_fixture() -> list[dict[str, object]]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _theme_packet(links: list[dict[str, object]]) -> ThemeLinkPacket:
    return ThemeLinkPacket.model_validate(
        {
            "theme_id": "fed_rate_cut_june_2026",
            "matched_polymarket_markets": links,
            "matched_assets": [],
            "matched_entities": [],
            "ambiguity_flags": [],
            "confidence_score": 0.9,
            "explanation": "Fixture theme link packet for evidence assembly tests.",
        }
    )


def _link(
    *,
    condition_id: str | None = None,
    market_slug: str | None = None,
    event_slug: str | None = None,
) -> dict[str, object]:
    return {
        "condition_id": condition_id,
        "market_slug": market_slug,
        "event_slug": event_slug,
        "outcome_map": {"Yes": "up", "No": "down"},
        "confidence": 0.9,
        "link_basis": "manual",
        "notes": "Evidence assembly test link.",
    }
