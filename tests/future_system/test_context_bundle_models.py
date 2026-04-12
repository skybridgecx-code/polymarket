"""Model validation tests for future_system.context_bundle contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.models import BundleQualitySummary, OpportunityContextBundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.theme_graph.models import ThemeLinkPacket
from pydantic import ValidationError

_FIXTURE_PATH = Path("tests/fixtures/future_system/context_bundle/context_bundle_inputs.json")


def test_context_bundle_models_accept_valid_payloads() -> None:
    case = _cases()["strong_complete"]
    quality = BundleQualitySummary.model_validate(
        {
            "completeness_score": 1.0,
            "freshness_score": 0.87,
            "confidence_score": 0.859,
            "conflict_score": 0.127,
            "component_statuses": {
                "theme_link": "present",
                "polymarket_evidence": "present",
                "divergence": "present",
                "crypto_evidence": "present",
                "comparison": "present",
                "news_evidence": "present",
                "candidate": "present",
            },
            "flags": [],
        }
    )
    bundle = OpportunityContextBundle.model_validate(
        {
            "theme_id": case["theme_link"].theme_id,
            "title": "Crypto Regulation Signal",
            "theme_link": case["theme_link"].model_dump(),
            "polymarket_evidence": case["polymarket_evidence"].model_dump(),
            "divergence": case["divergence"].model_dump(),
            "crypto_evidence": case["crypto_evidence"].model_dump(),
            "comparison": case["comparison"].model_dump(),
            "news_evidence": case["news_evidence"].model_dump(),
            "candidate": case["candidate"].model_dump(),
            "quality": quality.model_dump(),
            "operator_summary": "Deterministic operator summary.",
            "flags": [],
        }
    )

    assert bundle.theme_id == "theme_ctx_strong"
    assert bundle.quality.completeness_score == 1.0


def test_context_bundle_models_reject_invalid_bounded_scores() -> None:
    with pytest.raises(ValidationError):
        BundleQualitySummary.model_validate(
            {
                "completeness_score": 1.2,
                "freshness_score": 0.6,
                "confidence_score": 0.5,
                "conflict_score": 0.4,
                "component_statuses": {"theme_link": "present"},
                "flags": [],
            }
        )


def test_context_bundle_models_reject_invalid_component_statuses() -> None:
    with pytest.raises(ValidationError):
        BundleQualitySummary.model_validate(
            {
                "completeness_score": 0.8,
                "freshness_score": 0.6,
                "confidence_score": 0.5,
                "conflict_score": 0.4,
                "component_statuses": {"theme_link": "available"},
                "flags": [],
            }
        )


def _cases() -> dict[str, dict[str, object]]:
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
