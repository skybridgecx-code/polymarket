from __future__ import annotations

import asyncio
import json
from pathlib import Path

from polymarket_arb.config import Settings
from polymarket_arb.services.paper_trade_service import PaperTradeService


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _settings(tmp_path: Path) -> Settings:
    settings = Settings(
        DATA_DIR=tmp_path / "data",
        STATE_DIR=tmp_path / "state",
        POLY_GAMMA_BASE_URL="https://gamma-api.polymarket.com",
        POLY_CLOB_BASE_URL="https://clob.polymarket.com",
        POLY_DATA_BASE_URL="https://data-api.polymarket.com",
        POLY_WS_MARKET_URL="wss://ws-subscriptions-clob.polymarket.com/ws/market",
    )
    settings.ensure_directories()
    return settings


def _load_reports(tmp_path: Path) -> list[dict[str, object]]:
    fixture_path = Path("tests/fixtures/scenarios/phase7b_paper_trade.json")
    payload = _load_json(fixture_path)
    assert isinstance(payload, dict)

    service = PaperTradeService(_settings(tmp_path))
    return asyncio.run(
        service.build_paper_trade_rows(
            limit=10,
            fixture_path=str(fixture_path),
        )
    )


def _report_by_event_slug(
    reports: list[dict[str, object]],
    *,
    event_slug: str,
) -> dict[str, object]:
    for report in reports:
        reference = str(report["source_opportunity_reference"])
        if reference.startswith(f"{event_slug}:"):
            return report
    raise AssertionError(f"Missing report for {event_slug=}")


def test_paper_trade_service_accepts_plan_with_explicit_slippage_and_simulation(
    tmp_path: Path,
) -> None:
    reports = _load_reports(tmp_path)
    report = _report_by_event_slug(reports, event_slug="phase7b-accepted-complement")

    assert report["status"] == "accepted"
    assert report["rejection_reason"] is None
    assert report["plan_id"] == (
        "paper:phase7b-accepted-complement:binary_complement:pt_yes_1+pt_no_1:size=10"
    )
    assert report["proposed_size"] == "10"
    assert report["risk_flags"] == [
        "multi_leg_bundle",
        "size_clipped_to_plan_limit",
        "source_candidate_accepted",
    ]

    slippage = report["slippage_assumption"]
    assert isinstance(slippage, dict)
    assert slippage["total_bps"] == 22

    policy_decision = report["policy_decision"]
    assert isinstance(policy_decision, dict)
    assert policy_decision["decision"] == "allow"
    assert policy_decision["decision_reason"] == "passes_policy"
    assert policy_decision["observed_slippage_bps"] == 22
    assert policy_decision["manual_override_status"] == "not_requested"

    simulated_result = report["simulated_result"]
    assert isinstance(simulated_result, dict)
    assert simulated_result["simulated_net_edge_cents"] == "93.07"


def test_paper_trade_service_preserves_rejected_source_opportunity(tmp_path: Path) -> None:
    reports = _load_reports(tmp_path)
    report = _report_by_event_slug(reports, event_slug="phase7b-source-rejected")

    assert report["status"] == "rejected"
    assert report["rejection_reason"] == "source_opportunity_rejected"
    assert report["risk_flags"] == ["source_candidate_rejected"]
    assert report["simulated_result"] is None
    policy_decision = report["policy_decision"]
    assert isinstance(policy_decision, dict)
    assert policy_decision["decision"] == "deny"
    assert policy_decision["decision_reason"] == "upstream_result_rejected"


def test_paper_trade_service_rejects_thin_edge_and_low_capacity_plans(tmp_path: Path) -> None:
    reports = _load_reports(tmp_path)

    thin_edge = _report_by_event_slug(reports, event_slug="phase7b-thin-edge")
    assert thin_edge["status"] == "rejected"
    assert thin_edge["rejection_reason"] == "kill_switch_simulated_edge_below_buffer"
    assert "configured safety buffer" in str(thin_edge["explanation"])
    assert thin_edge["risk_flags"] == [
        "multi_leg_bundle",
        "size_clipped_to_plan_limit",
        "source_candidate_accepted",
        "thin_simulated_edge",
    ]
    assert thin_edge["simulated_result"] is not None
    thin_edge_policy = thin_edge["policy_decision"]
    assert isinstance(thin_edge_policy, dict)
    assert thin_edge_policy["decision"] == "deny"
    assert thin_edge_policy["decision_reason"] == "upstream_result_rejected"

    low_capacity = _report_by_event_slug(reports, event_slug="phase7b-low-capacity")
    assert low_capacity["status"] == "rejected"
    assert low_capacity["rejection_reason"] == "proposed_size_below_minimum"
    assert low_capacity["risk_flags"] == ["capacity_below_policy_floor"]
    assert low_capacity["simulated_result"] is None
    low_capacity_policy = low_capacity["policy_decision"]
    assert isinstance(low_capacity_policy, dict)
    assert low_capacity_policy["decision"] == "deny"
    assert low_capacity_policy["decision_reason"] == "upstream_result_rejected"


def test_paper_trade_service_outputs_operator_validation_fields_for_every_row(
    tmp_path: Path,
) -> None:
    reports = _load_reports(tmp_path)

    assert len(reports) == 4
    for report in reports:
        assert set(report) >= {
            "status",
            "rejection_reason",
            "explanation",
            "risk_flags",
            "simulated_result",
            "policy_decision",
        }
        assert "status" in report
        assert "rejection_reason" in report
        assert "explanation" in report
        assert "risk_flags" in report
        assert "simulated_result" in report
        assert "policy_decision" in report

        policy_decision = report["policy_decision"]
        assert isinstance(policy_decision, dict)
        assert policy_decision["decision"] in {"allow", "hold", "deny"}
