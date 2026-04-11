"""Model validation tests for future_system.theme_graph."""

from __future__ import annotations

from copy import deepcopy

import pytest
from future_system.theme_graph.models import ThemeDefinition
from pydantic import ValidationError


def test_theme_definition_accepts_valid_payload() -> None:
    theme = ThemeDefinition.model_validate(_valid_theme_payload())

    assert theme.theme_id == "theme_models_valid"
    assert theme.aliases == ["theme models valid", "valid models theme"]
    assert theme.polymarket_links[0].confidence == 0.95


def test_theme_definition_rejects_invalid_enum_and_range_values() -> None:
    invalid_status = _valid_theme_payload()
    invalid_status["status"] = "unsupported"

    with pytest.raises(ValidationError):
        ThemeDefinition.model_validate(invalid_status)

    invalid_confidence = _valid_theme_payload()
    invalid_confidence["polymarket_links"][0]["confidence"] = 1.2

    with pytest.raises(ValidationError):
        ThemeDefinition.model_validate(invalid_confidence)

    invalid_relevance = _valid_theme_payload()
    invalid_relevance["asset_links"][0]["relevance"] = -0.01

    with pytest.raises(ValidationError):
        ThemeDefinition.model_validate(invalid_relevance)


def test_theme_definition_rejects_invalid_date_ordering() -> None:
    invalid_dates = _valid_theme_payload()
    invalid_dates["start_at"] = "2026-12-31T00:00:00Z"
    invalid_dates["expected_resolution_at"] = "2026-01-01T00:00:00Z"

    with pytest.raises(ValidationError):
        ThemeDefinition.model_validate(invalid_dates)



def _valid_theme_payload() -> dict[str, object]:
    payload: dict[str, object] = {
        "theme_id": "theme_models_valid",
        "title": "Theme Models Valid",
        "description": "Validation payload for theme graph models.",
        "status": "active",
        "category": "other",
        "start_at": "2026-01-01T00:00:00Z",
        "expected_resolution_at": "2026-06-01T00:00:00Z",
        "primary_question": "Will model validation remain deterministic?",
        "aliases": ["theme models valid", "valid models theme"],
        "polymarket_links": [
            {
                "condition_id": "0xmodelsvalid",
                "market_slug": "theme-models-valid-market",
                "event_slug": "theme-models-valid-event",
                "outcome_map": {"Yes": "valid", "No": "invalid"},
                "confidence": 0.95,
                "link_basis": "manual",
                "notes": "Model-level validation fixture.",
            }
        ],
        "asset_links": [
            {
                "symbol": "ABC",
                "asset_type": "equity",
                "relevance": 0.6,
                "role": "context_only",
                "direction_if_theme_up": "mixed",
                "link_basis": "manual",
            }
        ],
        "news_entities": [
            {
                "entity_name": "Validation Institute",
                "entity_type": "institution",
                "relevance": 0.7,
                "required": True,
            }
        ],
        "relationship_templates": [
            {
                "trigger": "Validation trigger",
                "supporting_moves": ["Schema passes"],
                "contradicting_moves": ["Schema fails"],
                "notes": "Model test relationship.",
            }
        ],
        "review_required": True,
    }
    return deepcopy(payload)
