"""Builder behavior tests for deterministic opportunity context bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import (
    build_opportunity_context_bundle,
    export_opportunity_context_bundle,
)
from future_system.context_bundle.models import ContextBundleError
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.theme_graph.models import ThemeLinkPacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/context_bundle/context_bundle_inputs.json")


def test_matching_theme_ids_are_required() -> None:
    strong = _cases()["strong_complete"]
    mismatched_candidate = strong["candidate"].model_copy(update={"theme_id": "different_theme"})

    with pytest.raises(ContextBundleError):
        build_opportunity_context_bundle(
            theme_link_packet=strong["theme_link"],
            polymarket_evidence_packet=strong["polymarket_evidence"],
            divergence_packet=strong["divergence"],
            crypto_evidence_packet=strong["crypto_evidence"],
            comparison_packet=strong["comparison"],
            news_evidence_packet=strong["news_evidence"],
            candidate_packet=mismatched_candidate,
        )


def test_bundle_builds_successfully_from_valid_canonical_packets() -> None:
    strong = _cases()["strong_complete"]

    bundle = _build_bundle(strong)

    assert bundle.theme_id == "theme_ctx_strong"
    assert bundle.candidate.posture == "candidate"
    assert bundle.comparison.alignment == "aligned"


def test_bundle_scores_are_bounded_for_all_cases() -> None:
    for case in _cases().values():
        bundle = _build_bundle(case)

        assert 0.0 <= bundle.quality.completeness_score <= 1.0
        assert 0.0 <= bundle.quality.freshness_score <= 1.0
        assert 0.0 <= bundle.quality.confidence_score <= 1.0
        assert 0.0 <= bundle.quality.conflict_score <= 1.0


def test_component_statuses_are_deterministic() -> None:
    cases = _cases()

    strong = _build_bundle(cases["strong_complete"])
    weak = _build_bundle(cases["weak_incomplete"])
    conflicted = _build_bundle(cases["conflicted"])

    assert strong.quality.component_statuses == {
        "theme_link": "present",
        "polymarket_evidence": "present",
        "divergence": "present",
        "crypto_evidence": "present",
        "comparison": "present",
        "news_evidence": "present",
        "candidate": "present",
    }
    assert weak.quality.component_statuses == {
        "theme_link": "partial",
        "polymarket_evidence": "partial",
        "divergence": "partial",
        "crypto_evidence": "partial",
        "comparison": "partial",
        "news_evidence": "partial",
        "candidate": "partial",
    }
    assert conflicted.quality.component_statuses == {
        "theme_link": "present",
        "polymarket_evidence": "present",
        "divergence": "present",
        "crypto_evidence": "present",
        "comparison": "present",
        "news_evidence": "present",
        "candidate": "present",
    }


def test_important_flags_propagate_appropriately() -> None:
    cases = _cases()

    weak_bundle = _build_bundle(cases["weak_incomplete"])
    conflicted_bundle = _build_bundle(cases["conflicted"])

    assert "context_incomplete" in weak_bundle.flags
    assert "stale_context" in weak_bundle.flags
    assert "weak_news_context" in weak_bundle.flags
    assert "weak_crypto_context" in weak_bundle.flags
    assert "candidate_insufficient" in weak_bundle.flags

    assert "cross_market_conflict" in conflicted_bundle.flags
    assert "high_internal_divergence" in conflicted_bundle.flags


def test_export_shape_is_deterministic() -> None:
    strong = _cases()["strong_complete"]

    bundle = _build_bundle(strong)
    export_a = export_opportunity_context_bundle(bundle)
    export_b = export_opportunity_context_bundle(bundle)

    assert export_a == export_b
    assert list(export_a.keys()) == [
        "theme_id",
        "title",
        "theme_link",
        "polymarket_evidence",
        "divergence",
        "crypto_evidence",
        "comparison",
        "news_evidence",
        "candidate",
        "quality",
        "operator_summary",
        "flags",
    ]


def test_title_handling_is_deterministic() -> None:
    cases = _cases()

    strong_bundle = _build_bundle(cases["strong_complete"])
    weak_bundle = _build_bundle(cases["weak_incomplete"])

    assert strong_bundle.title == "Crypto Regulation Signal"
    assert weak_bundle.title is None


def _build_bundle(case: dict[str, Any]) -> Any:
    return build_opportunity_context_bundle(
        theme_link_packet=case["theme_link"],
        polymarket_evidence_packet=case["polymarket_evidence"],
        divergence_packet=case["divergence"],
        crypto_evidence_packet=case["crypto_evidence"],
        comparison_packet=case["comparison"],
        news_evidence_packet=case["news_evidence"],
        candidate_packet=case["candidate"],
    )


def _cases() -> dict[str, dict[str, Any]]:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        entry["case"]: {
            "theme_link": ThemeLinkPacket.model_validate(entry["theme_link"]),
            "polymarket_evidence": ThemeEvidencePacket.model_validate(entry["polymarket_evidence"]),
            "divergence": ThemeDivergencePacket.model_validate(entry["divergence"]),
            "crypto_evidence": ThemeCryptoEvidencePacket.model_validate(entry["crypto_evidence"]),
            "comparison": ThemeComparisonPacket.model_validate(entry["comparison"]),
            "news_evidence": ThemeNewsEvidencePacket.model_validate(entry["news_evidence"]),
            "candidate": CandidateSignalPacket.model_validate(entry["candidate"]),
        }
        for entry in payload
    }
