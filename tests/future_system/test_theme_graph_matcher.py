"""Matcher and linker behavior tests for future_system.theme_graph."""

from __future__ import annotations

from pathlib import Path

from future_system.theme_graph.linker import build_theme_link_packet
from future_system.theme_graph.loader import load_theme_definitions
from future_system.theme_graph.matcher import match_theme_candidates
from future_system.theme_graph.models import ThemeDefinition

_THEME_FIXTURE_DIR = Path("tests/fixtures/future_system/themes")


def test_exact_market_slug_match_works() -> None:
    themes = load_theme_definitions(_THEME_FIXTURE_DIR)

    result = match_theme_candidates(
        market_metadata={
            "market_slug": "will-fed-cut-rates-by-june-2026",
            "question": "Will Fed cut rates by June 2026?",
        },
        themes=themes,
    )

    assert result.confident_candidate is not None
    assert result.confident_candidate.theme.theme_id == "fed_rate_cut_june_2026"
    assert "market_slug_exact" in result.confident_candidate.reasons


def test_exact_event_slug_match_works_when_configured() -> None:
    themes = load_theme_definitions(_THEME_FIXTURE_DIR)

    result = match_theme_candidates(
        market_metadata={
            "event_slug": "us-presidential-election-2028",
            "question": "Who wins US election 2028?",
        },
        themes=themes,
    )

    assert result.confident_candidate is not None
    assert result.confident_candidate.theme.theme_id == "us_election_2028"
    assert "event_slug_exact" in result.confident_candidate.reasons


def test_condition_id_match_wins_over_other_slug_matches() -> None:
    themes = load_theme_definitions(_THEME_FIXTURE_DIR)

    result = match_theme_candidates(
        market_metadata={
            "condition_id": "0xbtcspotetfapproval",
            "market_slug": "will-fed-cut-rates-by-june-2026",
            "question": "Mixed metadata payload.",
        },
        themes=themes,
    )

    assert result.confident_candidate is not None
    assert result.confident_candidate.theme.theme_id == "btc_spot_etf_approval"
    assert "condition_id_exact" in result.confident_candidate.reasons


def test_ambiguous_case_emits_explicit_ambiguity_flags() -> None:
    theme_a = ThemeDefinition.model_validate(
        _ambiguous_theme_payload(theme_id="ambiguous_a", title="Ambiguous Theme A")
    )
    theme_b = ThemeDefinition.model_validate(
        _ambiguous_theme_payload(theme_id="ambiguous_b", title="Ambiguous Theme B")
    )

    result = match_theme_candidates(
        market_metadata={"market_slug": "ambiguous-market", "question": "Ambiguous market"},
        themes=[theme_b, theme_a],
    )

    assert result.confident_candidate is not None
    assert result.confident_candidate.theme.theme_id == "ambiguous_a"
    assert result.ambiguity_flags == ["multiple_strong_matches:ambiguous_a,ambiguous_b"]


def test_weak_unmatched_case_returns_no_confident_result() -> None:
    themes = load_theme_definitions(_THEME_FIXTURE_DIR)

    result = match_theme_candidates(
        market_metadata={
            "market_slug": "totally-unrelated-market",
            "question": "Will lunar soil moisture exceed threshold x9?",
            "description": "No overlap with known themes.",
        },
        themes=themes,
    )

    assert result.confident_candidate is None


def test_linker_emits_deterministic_theme_link_packet() -> None:
    themes = load_theme_definitions(_THEME_FIXTURE_DIR)

    result = match_theme_candidates(
        market_metadata={
            "market_slug": "will-fed-cut-rates-by-june-2026",
            "question": "Will Fed cut rates by June 2026?",
        },
        themes=themes,
    )
    packet_a = build_theme_link_packet(result)
    packet_b = build_theme_link_packet(result)

    assert packet_a is not None
    assert packet_b is not None
    assert packet_a.model_dump() == packet_b.model_dump()
    assert packet_a.theme_id == "fed_rate_cut_june_2026"
    assert packet_a.confidence_score == 0.9
    assert packet_a.matched_polymarket_markets[0].market_slug == "will-fed-cut-rates-by-june-2026"



def _ambiguous_theme_payload(*, theme_id: str, title: str) -> dict[str, object]:
    return {
        "theme_id": theme_id,
        "title": title,
        "description": "Ambiguity fixture theme.",
        "status": "active",
        "category": "other",
        "start_at": "2026-01-01T00:00:00Z",
        "expected_resolution_at": "2026-06-01T00:00:00Z",
        "primary_question": "Will ambiguous market resolve?",
        "aliases": [f"{theme_id} alias"],
        "polymarket_links": [
            {
                "condition_id": None,
                "market_slug": "ambiguous-market",
                "event_slug": None,
                "outcome_map": {"Yes": "up", "No": "down"},
                "confidence": 0.9,
                "link_basis": "manual",
                "notes": "Ambiguity fixture",
            }
        ],
        "asset_links": [
            {
                "symbol": "AMB",
                "asset_type": "equity",
                "relevance": 0.5,
                "role": "context_only",
                "direction_if_theme_up": "mixed",
                "link_basis": "manual",
            }
        ],
        "news_entities": [
            {
                "entity_name": "Ambiguous Entity",
                "entity_type": "institution",
                "relevance": 0.6,
                "required": False,
            }
        ],
        "relationship_templates": [
            {
                "trigger": "Ambiguous trigger",
                "supporting_moves": ["Move up"],
                "contradicting_moves": ["Move down"],
                "notes": "Ambiguous relationship",
            }
        ],
        "review_required": True,
    }
