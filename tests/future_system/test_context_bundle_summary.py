"""Summary behavior tests for deterministic opportunity context bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.context_bundle.summary import summarize_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.theme_graph.models import ThemeLinkPacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/context_bundle/context_bundle_inputs.json")


def test_operator_summary_string_is_deterministic() -> None:
    strong = _build_bundle(_cases()["strong_complete"])

    first = summarize_opportunity_context_bundle(strong)
    second = summarize_opportunity_context_bundle(strong)

    assert first == second
    assert first == (
        "theme_id=theme_ctx_strong; "
        "posture=candidate; "
        "alignment=aligned; "
        "completeness=1.000; "
        "freshness=0.870; "
        "confidence=0.859; "
        "conflict=0.127; "
        "flags=none."
    )


def test_summary_reflects_candidate_posture() -> None:
    weak = _build_bundle(_cases()["weak_incomplete"])

    summary = summarize_opportunity_context_bundle(weak)

    assert "posture=insufficient" in summary


def test_summary_reflects_comparison_alignment() -> None:
    conflicted = _build_bundle(_cases()["conflicted"])

    summary = summarize_opportunity_context_bundle(conflicted)

    assert "alignment=conflicted" in summary


def test_summary_reflects_bundle_flags() -> None:
    weak = _build_bundle(_cases()["weak_incomplete"])

    summary = summarize_opportunity_context_bundle(weak)

    assert "flags=candidate_insufficient,context_incomplete,stale_context." in summary


def test_weak_context_summary_remains_deterministic() -> None:
    weak = _build_bundle(_cases()["weak_incomplete"])

    summary = summarize_opportunity_context_bundle(weak)

    assert summary == (
        "theme_id=theme_ctx_weak; "
        "posture=insufficient; "
        "alignment=insufficient; "
        "completeness=0.500; "
        "freshness=0.337; "
        "confidence=0.320; "
        "conflict=0.556; "
        "flags=candidate_insufficient,context_incomplete,stale_context."
    )


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
