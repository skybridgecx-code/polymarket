from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from polymarket_arb.models.normalized import NormalizedWalletActivity
from polymarket_arb.relationships.engine import RelationshipEngine


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_reports() -> list[dict[str, object]]:
    fixture_path = Path("tests/fixtures/scenarios/phase4_relationships.json")
    payload = _load_json(fixture_path)
    assert isinstance(payload, dict)

    activities = [
        NormalizedWalletActivity.model_validate(item)
        for item in payload["activities"]
    ]
    reports = RelationshipEngine().build_relationship_reports(activities=activities)
    return [report.to_output() for report in reports]


def _report_by_wallets(
    reports: list[dict[str, object]],
    *,
    leader_wallet: str,
    follower_wallet: str,
) -> dict[str, object]:
    for report in reports:
        if (
            report["leader_wallet"] == leader_wallet
            and report["follower_wallet"] == follower_wallet
        ):
            return report
    raise AssertionError(f"Missing report for {leader_wallet=} {follower_wallet=}")


def test_relationship_engine_accepts_clear_repeated_follower_pattern() -> None:
    reports = _load_reports()
    report = _report_by_wallets(
        reports,
        leader_wallet="0xaaa0000000000000000000000000000000000001",
        follower_wallet="0xbbb0000000000000000000000000000000000002",
    )

    assert report["status"] == "accepted"
    assert report["rejection_reason"] is None
    assert report["matched_events_count"] == 3
    assert report["matched_legs_count"] == 3
    assert report["lag_summary_seconds"] == {"min": 30, "median": 45, "max": 60}
    assert report["confidence_score"] == "0.72"
    assert "repeatedly followed" in str(report["explanation"])
    assert len(cast(list[object], report["evidence"])) == 3


def test_relationship_engine_rejects_clear_non_copier_outside_lag_window() -> None:
    reports = _load_reports()
    report = _report_by_wallets(
        reports,
        leader_wallet="0xaaa0000000000000000000000000000000000001",
        follower_wallet="0xccc0000000000000000000000000000000000003",
    )

    assert report["status"] == "rejected"
    assert report["rejection_reason"] == "no_same_leg_matches"
    assert report["matched_events_count"] == 0
    assert report["matched_legs_count"] == 0
    assert report["evidence"] == []


def test_relationship_engine_rejects_bidirectional_overlap_as_ambiguous() -> None:
    reports = _load_reports()

    forward = _report_by_wallets(
        reports,
        leader_wallet="0xddd0000000000000000000000000000000000004",
        follower_wallet="0xeee0000000000000000000000000000000000005",
    )
    reverse = _report_by_wallets(
        reports,
        leader_wallet="0xeee0000000000000000000000000000000000005",
        follower_wallet="0xddd0000000000000000000000000000000000004",
    )

    assert forward["status"] == "rejected"
    assert reverse["status"] == "rejected"
    assert forward["rejection_reason"] == "ambiguous_bidirectional_overlap"
    assert reverse["rejection_reason"] == "ambiguous_bidirectional_overlap"
    assert forward["matched_events_count"] == 3
    assert reverse["matched_events_count"] == 3
    assert "ambiguous" in str(forward["explanation"]).lower()
