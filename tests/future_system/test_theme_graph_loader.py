"""Loader behavior tests for future_system.theme_graph."""

from __future__ import annotations

from pathlib import Path

import pytest
from future_system.theme_graph.loader import ThemeLoadError, load_theme_definitions

_THEME_FIXTURE_DIR = Path("tests/fixtures/future_system/themes")


def test_loader_reads_fixture_themes_in_deterministic_order() -> None:
    themes = load_theme_definitions(_THEME_FIXTURE_DIR)

    assert [theme.theme_id for theme in themes] == [
        "btc_spot_etf_approval",
        "fed_rate_cut_june_2026",
        "us_election_2028",
    ]


def test_loader_rejects_duplicate_theme_ids() -> None:
    fixture_a = _valid_yaml(theme_id="duplicate_theme", market_slug="dup-market-a")
    fixture_b = _valid_yaml(theme_id="duplicate_theme", market_slug="dup-market-b")

    tmp_dir = Path("tests/.tmp_theme_loader_duplicates")
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / "a.yaml").write_text(fixture_a, encoding="utf-8")
    (tmp_dir / "b.yaml").write_text(fixture_b, encoding="utf-8")

    try:
        with pytest.raises(ThemeLoadError, match="Duplicate theme_id"):
            load_theme_definitions(tmp_dir)
    finally:
        for path in tmp_dir.glob("*.yaml"):
            path.unlink()
        tmp_dir.rmdir()


def test_loader_rejects_malformed_yaml() -> None:
    tmp_dir = Path("tests/.tmp_theme_loader_malformed_yaml")
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / "bad.yaml").write_text("theme_id: [bad", encoding="utf-8")

    try:
        with pytest.raises(ThemeLoadError, match="Invalid YAML"):
            load_theme_definitions(tmp_dir)
    finally:
        for path in tmp_dir.glob("*.yaml"):
            path.unlink()
        tmp_dir.rmdir()


def test_loader_rejects_malformed_schema() -> None:
    malformed_schema = _valid_yaml(theme_id="schema_bad", market_slug="schema-bad")
    malformed_schema = malformed_schema.replace("status: active", "status: unknown")

    tmp_dir = Path("tests/.tmp_theme_loader_schema")
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / "bad_schema.yaml").write_text(malformed_schema, encoding="utf-8")

    try:
        with pytest.raises(ThemeLoadError, match="schema validation"):
            load_theme_definitions(tmp_dir)
    finally:
        for path in tmp_dir.glob("*.yaml"):
            path.unlink()
        tmp_dir.rmdir()



def _valid_yaml(*, theme_id: str, market_slug: str) -> str:
    return f"""
theme_id: {theme_id}
title: Loader Theme {theme_id}
description: Loader validation fixture.
status: active
category: other
start_at: \"2026-01-01T00:00:00Z\"
expected_resolution_at: \"2026-06-01T00:00:00Z\"
primary_question: Will this theme load correctly?
aliases:
  - loader alias {theme_id}
polymarket_links:
  - condition_id: \"0x{theme_id}\"
    market_slug: {market_slug}
    event_slug: loader-event
    outcome_map:
      \"Yes\": true_case
      \"No\": false_case
    confidence: 0.91
    link_basis: manual
    notes: Loader fixture.
asset_links:
  - symbol: LDR
    asset_type: equity
    relevance: 0.6
    role: context_only
    direction_if_theme_up: mixed
    link_basis: manual
news_entities:
  - entity_name: Loader Entity
    entity_type: institution
    relevance: 0.7
    required: true
relationship_templates:
  - trigger: Loader trigger
    supporting_moves:
      - Signal up
    contradicting_moves:
      - Signal down
    notes: Loader relationship.
review_required: true
""".strip()
