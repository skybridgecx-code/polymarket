"""Builder behavior tests for deterministic candidate signal packet construction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from future_system.candidates.builder import build_candidate_signal_packet
from future_system.candidates.models import CandidateBuildError
from future_system.comparison.models import ThemeComparisonPacket
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.theme_graph.models import ThemeLinkPacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/candidates/candidate_inputs.json")


def test_matching_theme_ids_are_required() -> None:
    strong_case = _cases()["strong_candidate"]
    mismatched_comparison = strong_case["comparison"].model_copy(
        update={"theme_id": "different_theme"}
    )

    with pytest.raises(CandidateBuildError):
        build_candidate_signal_packet(
            link_packet=strong_case["link"],
            evidence_packet=strong_case["evidence"],
            divergence_packet=strong_case["divergence"],
            crypto_packet=strong_case["crypto"],
            comparison_packet=mismatched_comparison,
        )


def test_strong_aligned_case_yields_candidate() -> None:
    case = _cases()["strong_candidate"]

    packet = build_candidate_signal_packet(
        link_packet=case["link"],
        evidence_packet=case["evidence"],
        divergence_packet=case["divergence"],
        crypto_packet=case["crypto"],
        comparison_packet=case["comparison"],
    )

    assert packet.posture == "candidate"
    assert packet.reason_codes == ["strong_cross_market_alignment"]


def test_weaker_case_yields_watch() -> None:
    case = _cases()["watch"]

    packet = build_candidate_signal_packet(
        link_packet=case["link"],
        evidence_packet=case["evidence"],
        divergence_packet=case["divergence"],
        crypto_packet=case["crypto"],
        comparison_packet=case["comparison"],
    )

    assert packet.posture == "watch"
    assert packet.reason_codes == ["weak_cross_market_alignment"]


def test_conflict_case_yields_high_conflict() -> None:
    case = _cases()["high_conflict"]

    packet = build_candidate_signal_packet(
        link_packet=case["link"],
        evidence_packet=case["evidence"],
        divergence_packet=case["divergence"],
        crypto_packet=case["crypto"],
        comparison_packet=case["comparison"],
    )

    assert packet.posture == "high_conflict"
    assert packet.reason_codes == ["cross_market_conflict", "high_internal_divergence"]


def test_insufficient_case_yields_insufficient() -> None:
    case = _cases()["insufficient"]

    packet = build_candidate_signal_packet(
        link_packet=case["link"],
        evidence_packet=case["evidence"],
        divergence_packet=case["divergence"],
        crypto_packet=case["crypto"],
        comparison_packet=case["comparison"],
    )

    assert packet.posture == "insufficient"


def test_reason_codes_are_deterministic() -> None:
    case = _cases()["watch"]

    first = build_candidate_signal_packet(
        link_packet=case["link"],
        evidence_packet=case["evidence"],
        divergence_packet=case["divergence"],
        crypto_packet=case["crypto"],
        comparison_packet=case["comparison"],
    )
    second = build_candidate_signal_packet(
        link_packet=case["link"],
        evidence_packet=case["evidence"],
        divergence_packet=case["divergence"],
        crypto_packet=case["crypto"],
        comparison_packet=case["comparison"],
    )

    assert first.reason_codes == second.reason_codes


def test_explanation_is_deterministic() -> None:
    case = _cases()["strong_candidate"]

    packet = build_candidate_signal_packet(
        link_packet=case["link"],
        evidence_packet=case["evidence"],
        divergence_packet=case["divergence"],
        crypto_packet=case["crypto"],
        comparison_packet=case["comparison"],
    )

    assert packet.explanation == (
        "posture=candidate; "
        "candidate_score=0.833; "
        "confidence_score=0.852; "
        "conflict_score=0.084; "
        "alignment=aligned; "
        "reasons=strong_cross_market_alignment."
    )


def test_important_upstream_flags_propagate_deterministically() -> None:
    conflict_case = _cases()["high_conflict"]
    insufficient_case = _cases()["insufficient"]

    conflict_packet = build_candidate_signal_packet(
        link_packet=conflict_case["link"],
        evidence_packet=conflict_case["evidence"],
        divergence_packet=conflict_case["divergence"],
        crypto_packet=conflict_case["crypto"],
        comparison_packet=conflict_case["comparison"],
    )
    insufficient_packet = build_candidate_signal_packet(
        link_packet=insufficient_case["link"],
        evidence_packet=insufficient_case["evidence"],
        divergence_packet=insufficient_case["divergence"],
        crypto_packet=insufficient_case["crypto"],
        comparison_packet=insufficient_case["comparison"],
    )

    assert "cross_market_conflict" in conflict_packet.flags
    assert "high_internal_dispersion" in conflict_packet.flags
    assert "missing_probability_inputs" in insufficient_packet.flags
    assert "weak_crypto_coverage" in insufficient_packet.flags


def _cases() -> dict[str, dict[str, Any]]:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        entry["case"]: {
            "link": ThemeLinkPacket.model_validate(entry["link_packet"]),
            "evidence": ThemeEvidencePacket.model_validate(entry["evidence_packet"]),
            "divergence": ThemeDivergencePacket.model_validate(entry["divergence_packet"]),
            "crypto": ThemeCryptoEvidencePacket.model_validate(entry["crypto_packet"]),
            "comparison": ThemeComparisonPacket.model_validate(entry["comparison_packet"]),
        }
        for entry in payload
    }
