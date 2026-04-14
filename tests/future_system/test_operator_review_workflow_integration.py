"""Integration tests for deterministic local operator review metadata workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from future_system.candidates.models import CandidateSignalPacket
from future_system.cli.review_artifacts import main
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.operator_review_models import OperatorReviewDecisionRecord
from future_system.operator_ui import create_operator_ui_app
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)


def test_cli_default_path_writes_no_companion_metadata_and_ui_shows_no_review_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-default"
    target_directory.mkdir()

    summary = _run_cli(
        capsys=capsys,
        context_source=context_source,
        target_directory=target_directory,
        analyst_mode="stub",
        initialize_operator_review=False,
    )
    run_id = Path(str(summary["json_file_path"])).stem
    metadata_path = target_directory / f"{run_id}.operator_review.json"
    assert not metadata_path.exists()

    client = TestClient(create_operator_ui_app(artifacts_root=target_directory))
    list_response = client.get("/")
    detail_response = client.get(f"/runs/{run_id}")

    assert list_response.status_code == 200
    assert run_id in list_response.text
    assert "no-review-metadata" in list_response.text

    assert detail_response.status_code == 200
    assert "Operator Review Metadata" in detail_response.text
    assert "Review Status</dt><dd>no-review-metadata" in detail_response.text


def test_cli_opt_in_writes_pending_companion_and_ui_renders_pending(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-with-review"
    target_directory.mkdir()

    summary = _run_cli(
        capsys=capsys,
        context_source=context_source,
        target_directory=target_directory,
        analyst_mode="stub",
        initialize_operator_review=True,
    )
    run_id = Path(str(summary["json_file_path"])).stem
    metadata_path = target_directory / f"{run_id}.operator_review.json"
    outside_path = tmp_path.parent / f"{run_id}.operator_review.json"

    assert metadata_path.exists()
    assert metadata_path.resolve().parent == target_directory.resolve()
    assert not outside_path.exists()

    record = OperatorReviewDecisionRecord.model_validate(
        json.loads(metadata_path.read_text(encoding="utf-8"))
    )
    assert record.review_status == "pending"
    assert record.operator_decision is None
    assert record.artifact.run_id == run_id
    assert record.artifact.status == "success"
    assert record.artifact.failure_stage is None

    client = TestClient(create_operator_ui_app(artifacts_root=target_directory))
    list_response = client.get("/")
    detail_response = client.get(f"/runs/{run_id}")

    assert list_response.status_code == 200
    assert run_id in list_response.text
    assert "pending" in list_response.text

    assert detail_response.status_code == 200
    assert "Operator Review Metadata" in detail_response.text
    assert "Review Status</dt><dd>pending" in detail_response.text
    assert "Operator Decision</dt><dd>none" in detail_response.text


def test_cli_failure_opt_in_preserves_failure_stage_through_file_and_ui(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-failure-with-review"
    target_directory.mkdir()

    summary = _run_cli(
        capsys=capsys,
        context_source=context_source,
        target_directory=target_directory,
        analyst_mode="reasoning_parse",
        initialize_operator_review=True,
    )
    run_id = Path(str(summary["json_file_path"])).stem
    metadata_path = target_directory / f"{run_id}.operator_review.json"
    record = OperatorReviewDecisionRecord.model_validate(
        json.loads(metadata_path.read_text(encoding="utf-8"))
    )

    assert record.review_status == "pending"
    assert record.artifact.status == "failed"
    assert record.artifact.export_kind == "analysis_failure_export"
    assert record.artifact.failure_stage == "reasoning_parse"

    artifact_json = json.loads(Path(str(summary["json_file_path"])).read_text(encoding="utf-8"))
    assert artifact_json["payload"]["failure_stage"] == "reasoning_parse"

    client = TestClient(create_operator_ui_app(artifacts_root=target_directory))
    list_response = client.get("/")
    detail_response = client.get(f"/runs/{run_id}")

    assert list_response.status_code == 200
    assert "FAILED (reasoning_parse)" in list_response.text
    assert "pending" in list_response.text

    assert detail_response.status_code == 200
    assert "FAILED (reasoning_parse)" in detail_response.text
    assert "Review Status</dt><dd>pending" in detail_response.text
    assert "reasoning_parse" in detail_response.text


def test_cli_opt_in_existing_companion_no_overwrite_behavior_is_preserved(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-existing-review"
    target_directory.mkdir()

    first_summary = _run_cli(
        capsys=capsys,
        context_source=context_source,
        target_directory=target_directory,
        analyst_mode="stub",
        initialize_operator_review=True,
    )
    run_id = Path(str(first_summary["json_file_path"])).stem
    metadata_path = target_directory / f"{run_id}.operator_review.json"
    existing = metadata_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "--context-source",
            str(context_source),
            "--target-directory",
            str(target_directory),
            "--analyst-mode",
            "stub",
            "--initialize-operator-review",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "operator_review_metadata_file_exists" in captured.err
    assert metadata_path.read_text(encoding="utf-8") == existing


def test_ui_bounds_malformed_companion_metadata_non_fatal_after_cli_generation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-malformed-review"
    target_directory.mkdir()

    summary = _run_cli(
        capsys=capsys,
        context_source=context_source,
        target_directory=target_directory,
        analyst_mode="stub",
        initialize_operator_review=True,
    )
    run_id = Path(str(summary["json_file_path"])).stem
    metadata_path = target_directory / f"{run_id}.operator_review.json"
    metadata_path.write_text("{malformed", encoding="utf-8")

    client = TestClient(create_operator_ui_app(artifacts_root=target_directory))
    list_response = client.get("/")
    detail_response = client.get(f"/runs/{run_id}")

    assert list_response.status_code == 200
    assert run_id in list_response.text
    assert "operator_review_metadata_invalid" in list_response.text
    assert "no-review-metadata" in list_response.text

    assert detail_response.status_code == 200
    assert "Operator Review Metadata" in detail_response.text
    assert "operator_review_metadata_invalid" in detail_response.text
    assert "no-review-metadata" in detail_response.text


def test_ui_rejects_out_of_root_companion_metadata_reads_via_symlink(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-out-of-root-metadata"
    target_directory.mkdir()

    summary = _run_cli(
        capsys=capsys,
        context_source=context_source,
        target_directory=target_directory,
        analyst_mode="stub",
        initialize_operator_review=False,
    )
    run_id = Path(str(summary["json_file_path"])).stem
    metadata_path = target_directory / f"{run_id}.operator_review.json"
    outside_path = tmp_path.parent / "outside.operator_review.json"

    outside_payload = {
        "record_kind": "operator_review_decision_record",
        "record_version": 1,
        "artifact": {
            "run_id": run_id,
            "theme_id": "theme_ctx_strong",
            "status": "success",
            "export_kind": "analysis_success_export",
            "failure_stage": None,
            "json_file_path": None,
            "markdown_file_path": None,
        },
        "review_status": "pending",
        "operator_decision": None,
        "review_notes_summary": None,
        "reviewer_identity": None,
        "decided_at_epoch_ns": None,
        "updated_at_epoch_ns": None,
        "run_flags_snapshot": [],
    }
    outside_path.write_text(
        json.dumps(outside_payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    metadata_path.symlink_to(outside_path)

    client = TestClient(create_operator_ui_app(artifacts_root=target_directory))
    list_response = client.get("/")
    detail_response = client.get(f"/runs/{run_id}")

    assert list_response.status_code == 200
    assert "operator_review_metadata_invalid" in list_response.text
    assert "resolves outside artifacts root" in list_response.text

    assert detail_response.status_code == 200
    assert "operator_review_metadata_invalid" in detail_response.text
    assert "resolves outside artifacts root" in detail_response.text


def _run_cli(
    *,
    capsys: pytest.CaptureFixture[str],
    context_source: Path,
    target_directory: Path,
    analyst_mode: str,
    initialize_operator_review: bool,
) -> dict[str, object]:
    args = [
        "--context-source",
        str(context_source),
        "--target-directory",
        str(target_directory),
        "--analyst-mode",
        analyst_mode,
    ]
    if initialize_operator_review:
        args.append("--initialize-operator-review")

    exit_code = main(args)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    return json.loads(captured.out)


def _write_context_source(tmp_path: Path) -> Path:
    payload = _bundle("strong_complete").model_dump(mode="json")
    context_source = tmp_path / "context_bundle.json"
    context_source.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return context_source


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
