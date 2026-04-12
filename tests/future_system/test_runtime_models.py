"""Model validation tests for future_system.runtime contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.runtime.models import AnalysisRunPacket
from future_system.runtime.runner import run_analysis_pipeline
from future_system.runtime.stub_analyst import DeterministicStubAnalyst
from future_system.theme_graph.models import ThemeLinkPacket
from pydantic import ValidationError

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_RUNTIME_FIXTURE_PATH = Path("tests/fixtures/future_system/runtime/runtime_inputs.json")


def test_runtime_models_accept_valid_payloads() -> None:
    packet = _successful_run_packet()

    validated = AnalysisRunPacket.model_validate(packet.model_dump(mode="json"))

    assert validated.theme_id == packet.theme_id
    assert validated.status == "success"


def test_invalid_status_is_rejected() -> None:
    payload = _successful_run_packet().model_dump(mode="json")
    payload["status"] = "completed"

    with pytest.raises(ValidationError):
        AnalysisRunPacket.model_validate(payload)


def test_required_fields_are_enforced() -> None:
    missing_reasoning = _successful_run_packet().model_dump(mode="json")
    del missing_reasoning["reasoning_output"]

    with pytest.raises(ValidationError):
        AnalysisRunPacket.model_validate(missing_reasoning)

    blank_summary = _successful_run_packet().model_dump(mode="json")
    blank_summary["run_summary"] = "  "

    with pytest.raises(ValidationError):
        AnalysisRunPacket.model_validate(blank_summary)


def _successful_run_packet() -> AnalysisRunPacket:
    runtime_case = _runtime_case("success_strong")
    bundle = _bundle(runtime_case["context_bundle_case"])
    return run_analysis_pipeline(context_bundle=bundle, analyst=DeterministicStubAnalyst())


def _runtime_case(case_name: str) -> dict[str, Any]:
    payload = json.loads(_RUNTIME_FIXTURE_PATH.read_text(encoding="utf-8"))
    for item in payload:
        if item["case"] == case_name:
            return dict(item)
    raise AssertionError(f"Missing runtime fixture case: {case_name}")


def _bundle(case_name: str) -> Any:
    case = _context_cases()[case_name]
    return build_opportunity_context_bundle(
        theme_link_packet=case["theme_link"],
        polymarket_evidence_packet=case["polymarket_evidence"],
        divergence_packet=case["divergence"],
        crypto_evidence_packet=case["crypto_evidence"],
        comparison_packet=case["comparison"],
        news_evidence_packet=case["news_evidence"],
        candidate_packet=case["candidate"],
    )


def _context_cases() -> dict[str, dict[str, Any]]:
    payload = json.loads(_CONTEXT_FIXTURE_PATH.read_text(encoding="utf-8"))
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
