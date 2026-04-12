"""Builder behavior tests for deterministic reasoning input packet construction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.reasoning_contracts.builder import PROMPT_VERSION, build_reasoning_input_packet
from future_system.theme_graph.models import ThemeLinkPacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/context_bundle/context_bundle_inputs.json")


def test_reasoning_input_packet_builds_from_context_bundle() -> None:
    bundle = _bundle("strong_complete")

    packet = build_reasoning_input_packet(bundle=bundle)

    assert packet.theme_id == "theme_ctx_strong"
    assert packet.candidate_posture == "candidate"
    assert packet.comparison_alignment == "aligned"


def test_theme_id_title_and_operator_summary_carry_through() -> None:
    bundle = _bundle("strong_complete")

    packet = build_reasoning_input_packet(bundle=bundle)

    assert packet.theme_id == bundle.theme_id
    assert packet.title == bundle.title
    assert packet.operator_summary == bundle.operator_summary


def test_structured_facts_are_compact_and_stable() -> None:
    bundle = _bundle("strong_complete")

    packet = build_reasoning_input_packet(bundle=bundle)

    assert list(packet.structured_facts.keys()) == [
        "candidate_posture",
        "comparison_alignment",
        "candidate_score",
        "confidence_score",
        "conflict_score",
        "primary_market_slug",
        "primary_symbol",
        "news_matched_article_count",
        "news_official_source_present",
        "bundle_completeness_score",
        "bundle_key_flags",
    ]
    assert packet.structured_facts == {
        "candidate_posture": "candidate",
        "comparison_alignment": "aligned",
        "candidate_score": 0.84,
        "confidence_score": 0.86,
        "conflict_score": 0.12,
        "primary_market_slug": "crypto-regulation-signal",
        "primary_symbol": "BTC-PERP",
        "news_matched_article_count": 2,
        "news_official_source_present": True,
        "bundle_completeness_score": 1.0,
        "bundle_key_flags": [],
    }


def test_prompt_version_is_deterministic() -> None:
    strong_bundle = _bundle("strong_complete")
    weak_bundle = _bundle("weak_incomplete")

    strong_packet = build_reasoning_input_packet(bundle=strong_bundle)
    weak_packet = build_reasoning_input_packet(bundle=weak_bundle)

    assert strong_packet.prompt_version == PROMPT_VERSION == "v1"
    assert weak_packet.prompt_version == PROMPT_VERSION == "v1"


def _bundle(case_name: str) -> Any:
    case = _cases()[case_name]
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
