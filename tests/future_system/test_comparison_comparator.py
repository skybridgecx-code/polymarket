"""Comparator behavior tests for deterministic cross-market comparison."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.comparison.comparator import compare_theme_evidence_packets
from future_system.comparison.models import ComparisonError
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.evidence.models import ThemeEvidencePacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/comparison/theme_comparison_inputs.json")


def test_matching_theme_ids_are_required() -> None:
    aligned = _cases()["aligned"]
    mismatched_crypto = aligned["crypto"].model_copy(update={"theme_id": "different_theme"})

    with pytest.raises(ComparisonError):
        compare_theme_evidence_packets(
            polymarket_packet=aligned["polymarket"],
            crypto_packet=mismatched_crypto,
        )


def test_aligned_case_produces_aligned_alignment() -> None:
    case = _cases()["aligned"]

    packet = compare_theme_evidence_packets(
        polymarket_packet=case["polymarket"],
        crypto_packet=case["crypto"],
    )

    assert packet.alignment == "aligned"
    assert packet.flags == []


def test_weaker_case_produces_weakly_aligned_alignment() -> None:
    case = _cases()["weakly_aligned"]

    packet = compare_theme_evidence_packets(
        polymarket_packet=case["polymarket"],
        crypto_packet=case["crypto"],
    )

    assert packet.alignment == "weakly_aligned"


def test_directional_mismatch_produces_conflicted_alignment() -> None:
    case = _cases()["conflicted"]

    packet = compare_theme_evidence_packets(
        polymarket_packet=case["polymarket"],
        crypto_packet=case["crypto"],
    )

    assert packet.alignment == "conflicted"
    assert packet.flags == ["cross_market_conflict"]


def test_unknown_family_direction_produces_insufficient_alignment() -> None:
    case = _cases()["insufficient"]

    packet = compare_theme_evidence_packets(
        polymarket_packet=case["polymarket"],
        crypto_packet=case["crypto"],
    )

    assert packet.alignment == "insufficient"
    assert packet.flags == [
        "crypto_unknown_direction",
        "polymarket_unknown_direction",
        "stale_crypto_evidence",
        "stale_polymarket_evidence",
        "weak_crypto_coverage",
    ]


def test_packet_flags_are_deterministic() -> None:
    case = _cases()["insufficient"]

    first = compare_theme_evidence_packets(
        polymarket_packet=case["polymarket"],
        crypto_packet=case["crypto"],
    )
    second = compare_theme_evidence_packets(
        polymarket_packet=case["polymarket"],
        crypto_packet=case["crypto"],
    )

    assert first.model_dump() == second.model_dump()


def test_explanation_string_is_deterministic() -> None:
    case = _cases()["aligned"]

    packet = compare_theme_evidence_packets(
        polymarket_packet=case["polymarket"],
        crypto_packet=case["crypto"],
    )

    assert packet.explanation == (
        "polymarket_direction=bullish; "
        "crypto_direction=bullish; "
        "alignment=aligned; "
        "agreement_score=0.934; "
        "confidence_score=0.907; "
        "flags=none."
    )


def _cases() -> dict[str, dict[str, ThemeEvidencePacket | ThemeCryptoEvidencePacket]]:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        entry["case"]: {
            "polymarket": ThemeEvidencePacket.model_validate(entry["polymarket_packet"]),
            "crypto": ThemeCryptoEvidencePacket.model_validate(entry["crypto_packet"]),
        }
        for entry in payload
    }
