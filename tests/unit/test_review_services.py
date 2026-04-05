from __future__ import annotations

import asyncio
import json
from pathlib import Path

from polymarket_arb.config import Settings
from polymarket_arb.models.review import ReviewPacket
from polymarket_arb.review import ReplayEvaluationService, ReviewPacketService


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


def test_review_packet_service_builds_deterministic_packets_for_all_subjects(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    service = ReviewPacketService(settings)
    fixture_path = "tests/fixtures/scenarios/phase8_review_records_baseline.json"

    opportunities_packet = asyncio.run(
        service.build_packet(packet_type="opportunities", limit=10, fixture_path=fixture_path)
    )
    assert opportunities_packet.packet_type == "opportunities"
    assert opportunities_packet.created_at is None
    assert opportunities_packet.summarized_findings == {
        "accepted_count": 1,
        "rejected_count": 1,
        "total_records": 2,
    }
    assert opportunities_packet.status == "ready"
    assert "created_at_unavailable" in opportunities_packet.notes

    relationships_packet = asyncio.run(
        service.build_packet(packet_type="relationships", limit=10, fixture_path=fixture_path)
    )
    assert relationships_packet.packet_type == "relationships"
    assert relationships_packet.created_at == "2026-01-01T00:00:00Z"
    assert relationships_packet.raw_result_references == [
        "0x1111000000000000000000000000000000000001:0x2222000000000000000000000000000000000002:same_leg_same_side_lag",
        "0x3333000000000000000000000000000000000003:0x4444000000000000000000000000000000000004:same_leg_same_side_lag",
    ]

    paper_trade_packet = asyncio.run(
        service.build_packet(packet_type="paper_trade", limit=10, fixture_path=fixture_path)
    )
    assert paper_trade_packet.packet_type == "paper_trade"
    assert paper_trade_packet.created_at is None
    assert paper_trade_packet.raw_result_references == [
        "paper:review-plan-1",
        "paper:review-plan-2",
    ]


def test_replay_evaluation_service_reports_explicit_drift(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    service = ReviewPacketService(settings)
    evaluator = ReplayEvaluationService()

    baseline_packet = asyncio.run(
        service.build_packet(
            packet_type="paper_trade",
            limit=10,
            fixture_path="tests/fixtures/scenarios/phase8_review_records_baseline.json",
        )
    )
    candidate_packet = asyncio.run(
        service.build_packet(
            packet_type="paper_trade",
            limit=10,
            fixture_path="tests/fixtures/scenarios/phase8_review_records_candidate.json",
        )
    )

    baseline_path = tmp_path / "baseline_packet.json"
    candidate_path = tmp_path / "candidate_packet.json"
    baseline_path.write_text(json.dumps(baseline_packet.to_output(), indent=2, sort_keys=True))
    candidate_path.write_text(json.dumps(candidate_packet.to_output(), indent=2, sort_keys=True))

    evaluation_payload = evaluator.evaluate_packet_paths(
        baseline_path=str(baseline_path),
        candidate_path=str(candidate_path),
    )
    evaluation = ReviewPacket.model_validate(baseline_packet.to_output())
    assert evaluation.packet_type == "paper_trade"

    assert evaluation_payload["subject_type"] == "paper_trade"
    assert evaluation_payload["compared_records_count"] == 3
    assert evaluation_payload["matches_count"] == 1
    assert evaluation_payload["mismatches_count"] == 2
    assert evaluation_payload["status"] == "fail"
    assert (
        "field_mismatch:paper:review-plan-2:explanation"
        in evaluation_payload["drift_reasons"]
    )
    assert (
        "field_mismatch:paper:review-plan-2:rejection_reason"
        in evaluation_payload["drift_reasons"]
    )
    assert "field_mismatch:paper:review-plan-2:status" in evaluation_payload["drift_reasons"]
    assert "missing_in_baseline:paper:review-plan-3" in evaluation_payload["drift_reasons"]
    assert "Compared 3 records" in evaluation_payload["explanation"]

    pass_payload = evaluator.evaluate_packet_paths(
        baseline_path=str(baseline_path),
        candidate_path=str(baseline_path),
    )
    assert pass_payload["status"] == "pass"
    assert pass_payload["matches_count"] == 2
    assert pass_payload["mismatches_count"] == 0
    assert pass_payload["drift_reasons"] == []


def test_review_services_match_operator_validation_output_shapes(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    service = ReviewPacketService(settings)
    evaluator = ReplayEvaluationService()

    packet_output = asyncio.run(
        service.build_packet_output(
            packet_type="paper_trade",
            limit=10,
            fixture_path="tests/fixtures/scenarios/phase8_review_records_baseline.json",
        )
    )

    assert set(packet_output) >= {
        "packet_id",
        "packet_type",
        "created_at",
        "source_references",
        "summarized_findings",
        "status",
        "notes",
    }
    assert packet_output["packet_type"] == "paper_trade"
    assert isinstance(packet_output["source_references"], list)
    assert isinstance(packet_output["summarized_findings"], dict)
    assert packet_output["status"] == "ready"
    assert isinstance(packet_output["notes"], list)

    baseline_packet = asyncio.run(
        service.build_packet(
            packet_type="paper_trade",
            limit=10,
            fixture_path="tests/fixtures/scenarios/phase8_review_records_baseline.json",
        )
    )
    candidate_packet = asyncio.run(
        service.build_packet(
            packet_type="paper_trade",
            limit=10,
            fixture_path="tests/fixtures/scenarios/phase8_review_records_candidate.json",
        )
    )

    replay_output = evaluator.evaluate_packets(
        baseline_packet=baseline_packet,
        candidate_packet=candidate_packet,
    ).to_output()

    assert set(replay_output) == {
        "evaluation_id",
        "subject_type",
        "compared_records_count",
        "matches_count",
        "mismatches_count",
        "drift_reasons",
        "status",
        "explanation",
    }
    assert replay_output["subject_type"] == "paper_trade"
    assert replay_output["status"] == "fail"
    assert isinstance(replay_output["drift_reasons"], list)
    assert replay_output["compared_records_count"] == 3
