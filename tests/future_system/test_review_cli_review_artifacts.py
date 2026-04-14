"""Deterministic tests for future_system.cli.review_artifacts entry surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from future_system.candidates.models import CandidateSignalPacket
from future_system.cli.review_artifacts import main
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.operator_review_models import OperatorReviewDecisionRecord
from future_system.runtime.models import AnalysisRunFailureStage
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)


def test_cli_review_artifacts_success_outputs_deterministic_summary_and_paths(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-success"
    target_directory.mkdir()

    exit_code = main(
        [
            "--context-source",
            str(context_source),
            "--target-directory",
            str(target_directory),
            "--analyst-mode",
            "stub",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""

    summary = json.loads(captured.out)
    assert summary["status"] == "success"
    assert summary["entry_kind"] == "analysis_success_review_entry"
    assert summary["theme_id"] == "theme_ctx_strong"
    assert summary["target_directory"] == str(target_directory.resolve())
    assert summary["failure_stage"] is None
    assert summary["run_flags"] == [
        "analysis_dry_run",
        "stub_analyst_used",
        "reasoning_parsed",
        "policy_computed",
    ]

    markdown_path = Path(str(summary["markdown_file_path"]))
    json_path = Path(str(summary["json_file_path"]))
    assert markdown_path.exists()
    assert json_path.exists()
    assert markdown_path.name == "theme_ctx_strong.analysis_success_export.md"
    assert json_path.name == "theme_ctx_strong.analysis_success_export.json"
    assert not (
        target_directory / "theme_ctx_strong.analysis_success_export.operator_review.json"
    ).exists()


def test_cli_review_artifacts_opt_in_initializes_pending_operator_review_metadata(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-with-review-metadata"
    target_directory.mkdir()

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

    assert exit_code == 0
    assert captured.err == ""

    summary = json.loads(captured.out)
    json_path = Path(str(summary["json_file_path"]))
    run_id = json_path.stem
    metadata_path = target_directory / f"{run_id}.operator_review.json"
    assert metadata_path.exists()

    record = OperatorReviewDecisionRecord.model_validate(
        json.loads(metadata_path.read_text(encoding="utf-8"))
    )
    assert record.review_status == "pending"
    assert record.operator_decision is None
    assert record.artifact.run_id == run_id
    assert record.artifact.status == "success"
    assert record.artifact.failure_stage is None
    assert record.artifact.json_file_path == str(json_path)
    assert record.artifact.markdown_file_path == str(summary["markdown_file_path"])


@pytest.mark.parametrize(
    ("analyst_mode", "expected_failure_stage", "expected_run_flags"),
    [
        ("analyst_timeout", "analyst_timeout", ["analysis_dry_run", "analyst_timeout"]),
        (
            "analyst_transport",
            "analyst_transport",
            ["analysis_dry_run", "analyst_transport_failed"],
        ),
        (
            "reasoning_parse",
            "reasoning_parse",
            ["analysis_dry_run", "reasoning_parse_failed"],
        ),
    ],
)
def test_cli_review_artifacts_failure_modes_preserve_stage_identity(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    analyst_mode: str,
    expected_failure_stage: AnalysisRunFailureStage,
    expected_run_flags: list[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / f"artifacts-{analyst_mode}"
    target_directory.mkdir()

    exit_code = main(
        [
            "--context-source",
            str(context_source),
            "--target-directory",
            str(target_directory),
            "--analyst-mode",
            analyst_mode,
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""

    summary = json.loads(captured.out)
    assert summary["status"] == "failed"
    assert summary["entry_kind"] == "analysis_failure_review_entry"
    assert summary["theme_id"] == "theme_ctx_strong"
    assert summary["target_directory"] == str(target_directory.resolve())
    assert summary["failure_stage"] == expected_failure_stage
    assert summary["run_flags"] == expected_run_flags

    markdown_path = Path(str(summary["markdown_file_path"]))
    json_path = Path(str(summary["json_file_path"]))
    assert markdown_path.name == (
        f"theme_ctx_strong.analysis_failure_export.{expected_failure_stage}.md"
    )
    assert json_path.name == (
        f"theme_ctx_strong.analysis_failure_export.{expected_failure_stage}.json"
    )
    markdown_text = markdown_path.read_text(encoding="utf-8")
    json_document = json.loads(json_path.read_text(encoding="utf-8"))
    assert f"- Failure Stage: `{expected_failure_stage}`" in markdown_text
    assert json_document["payload"]["failure_stage"] == expected_failure_stage
    assert "policy_decision" not in json_document["payload"]["json_payload"]


def test_cli_review_artifacts_opt_in_failure_mode_preserves_stage_in_review_metadata(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-failure-with-review-metadata"
    target_directory.mkdir()

    exit_code = main(
        [
            "--context-source",
            str(context_source),
            "--target-directory",
            str(target_directory),
            "--analyst-mode",
            "reasoning_parse",
            "--initialize-operator-review",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""

    summary = json.loads(captured.out)
    json_path = Path(str(summary["json_file_path"]))
    run_id = json_path.stem
    metadata_path = target_directory / f"{run_id}.operator_review.json"
    record = OperatorReviewDecisionRecord.model_validate(
        json.loads(metadata_path.read_text(encoding="utf-8"))
    )

    assert record.review_status == "pending"
    assert record.artifact.status == "failed"
    assert record.artifact.failure_stage == "reasoning_parse"
    assert record.artifact.export_kind == "analysis_failure_export"


def test_cli_review_artifacts_opt_in_refuses_to_overwrite_existing_review_metadata(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context_source = _write_context_source(tmp_path)
    target_directory = tmp_path / "artifacts-existing-review-metadata"
    target_directory.mkdir()
    metadata_path = (
        target_directory / "theme_ctx_strong.analysis_success_export.operator_review.json"
    )
    existing_payload = '{"existing":"metadata"}\n'
    metadata_path.write_text(existing_payload, encoding="utf-8")

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
    assert metadata_path.read_text(encoding="utf-8") == existing_payload


def test_cli_review_artifacts_fails_explicitly_for_invalid_context_source(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target_directory = tmp_path / "artifacts-invalid-context"
    target_directory.mkdir()
    missing_source = tmp_path / "missing-context.json"

    exit_code = main(
        [
            "--context-source",
            str(missing_source),
            "--target-directory",
            str(target_directory),
            "--analyst-mode",
            "stub",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "review_artifacts_cli_error: context_source must reference an existing file." in (
        captured.err
    )


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
