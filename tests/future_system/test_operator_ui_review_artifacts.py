"""Deterministic tests for future_system.operator_ui.review_artifacts read-only screen."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.operator_ui.review_artifacts import create_review_artifacts_operator_app
from future_system.runtime.models import AnalysisRunFailureStage
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_ARTIFACTS_ROOT_ENV = "FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT"
_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY = "operator_runs"


def test_operator_ui_lists_success_and_failure_runs_with_stage_context(tmp_path: Path) -> None:
    older_run = _write_success_run(tmp_path)
    newer_run = _write_failure_run(tmp_path, failure_stage="analyst_transport")
    _set_mtime_ns(tmp_path / f"{older_run}.json", timestamp_ns=1_700_000_000_000_000_000)
    _set_mtime_ns(tmp_path / f"{newer_run}.json", timestamp_ns=1_800_000_000_000_000_000)

    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))
    response = client.get("/")

    assert response.status_code == 200
    body = response.text
    assert "Review Artifacts" in body
    assert older_run in body
    assert newer_run in body
    assert body.index(newer_run) < body.index(older_run)
    assert "SUCCESS" in body
    assert "FAILED (analyst_transport)" in body
    assert "analyst_transport" in body


def test_operator_ui_detail_shows_markdown_and_json_content(tmp_path: Path) -> None:
    run_id = _write_failure_run(tmp_path, failure_stage="reasoning_parse")

    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))
    response = client.get(f"/runs/{run_id}")

    assert response.status_code == 200
    body = response.text
    assert "Review Artifact Detail" in body
    assert run_id in body
    assert "theme_ctx_strong" in body
    assert "reasoning_parse" in body
    assert "# Analysis Review Export" in body
    assert "&quot;failure_stage&quot;: &quot;reasoning_parse&quot;" in body
    assert "Back to runs" in body
    assert "FAILED (reasoning_parse)" in body
    assert "Run Metadata" in body
    assert "Outcome Summary" in body
    assert "Failure Context" in body
    assert "reasoning payload parsing failed" in body
    assert "Artifact Paths" in body
    assert "Artifact Content" in body
    assert "Markdown Content" in body
    assert "JSON Content" in body


def test_operator_ui_detail_fails_safely_when_markdown_is_missing(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_failure_export.analyst_timeout"
    _write_json_only_failure_run(tmp_path, run_id=run_id, failure_stage="analyst_timeout")

    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))
    response = client.get(f"/runs/{run_id}")

    assert response.status_code == 422
    assert "Run Read Error" in response.text
    assert "artifact_markdown_missing: markdown file is missing." in response.text
    assert "Back to runs" in response.text


def test_operator_ui_detail_fails_safely_for_invalid_json(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    (tmp_path / f"{run_id}.md").write_text("# Analysis Review Export\n", encoding="utf-8")
    (tmp_path / f"{run_id}.json").write_text("{invalid_json", encoding="utf-8")

    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))
    response = client.get(f"/runs/{run_id}")

    assert response.status_code == 422
    assert "Run Read Error" in response.text
    assert "artifact_json_invalid: malformed JSON content." in response.text


def test_operator_ui_list_shows_explicit_run_issues_for_invalid_files(tmp_path: Path) -> None:
    _write_success_run(tmp_path)
    (tmp_path / "bad-run.json").write_text("{invalid_json", encoding="utf-8")
    _write_json_only_failure_run(
        tmp_path,
        run_id="theme_ctx_strong.analysis_failure_export.analyst_timeout",
        failure_stage="analyst_timeout",
    )

    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))
    response = client.get("/")

    assert response.status_code == 200
    assert "Run Issues" in response.text
    assert "bad-run" in response.text
    assert "json_invalid" in response.text
    assert "markdown_missing" in response.text


def test_operator_ui_detail_handles_large_content_with_safe_truncation(tmp_path: Path) -> None:
    run_id = _write_large_run(tmp_path)
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))

    response = client.get(f"/runs/{run_id}")

    assert response.status_code == 200
    body = response.text
    assert "Markdown content display truncated for safety" in body
    assert "JSON content display truncated for safety" in body
    assert "TAIL_MARKDOWN_SENTINEL" not in body
    assert "TAIL_JSON_SENTINEL" not in body


def test_operator_ui_trigger_success_redirects_to_run_detail_and_writes_inside_root(
    tmp_path: Path,
) -> None:
    context_source = _write_context_source(tmp_path)
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))

    response = client.post(
        "/runs/trigger",
        data={"context_source": str(context_source), "analyst_mode": "stub"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert (
        location
        == "/runs/theme_ctx_strong.analysis_success_export"
        f"?created=1&target_subdirectory={_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY}"
    )

    detail = client.get(location)
    assert detail.status_code == 200
    assert "Review Artifact Detail" in detail.text
    assert "Trigger Result Summary" in detail.text
    assert "Run created via trigger and loaded." in detail.text
    assert "Run Outcome" in detail.text
    assert "Outcome Summary" in detail.text
    assert "Target Subdirectory" in detail.text
    assert "Artifact Directory" in detail.text
    assert _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY in detail.text
    assert "status" in detail.text

    target_root = tmp_path / _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY
    markdown_path = target_root / "theme_ctx_strong.analysis_success_export.md"
    json_path = target_root / "theme_ctx_strong.analysis_success_export.json"
    assert markdown_path.exists()
    assert json_path.exists()
    assert markdown_path.resolve().parent == target_root.resolve()
    assert json_path.resolve().parent == target_root.resolve()
    assert markdown_path.resolve().parent != tmp_path.resolve()
    assert json_path.resolve().parent != tmp_path.resolve()


@pytest.mark.parametrize(
    ("analyst_mode", "expected_failure_stage"),
    [
        ("analyst_timeout", "analyst_timeout"),
        ("analyst_transport", "analyst_transport"),
        ("reasoning_parse", "reasoning_parse"),
    ],
)
def test_operator_ui_trigger_failure_preserves_stage_and_handoff(
    tmp_path: Path,
    analyst_mode: str,
    expected_failure_stage: AnalysisRunFailureStage,
) -> None:
    context_source = _write_context_source(tmp_path)
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))

    response = client.post(
        "/runs/trigger",
        data={"context_source": str(context_source), "analyst_mode": analyst_mode},
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert (
        location
        == "/runs/theme_ctx_strong.analysis_failure_export."
        f"{expected_failure_stage}?created=1&target_subdirectory={_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY}"
    )

    detail = client.get(location)
    assert detail.status_code == 200
    assert "Outcome Summary" in detail.text
    assert "Failure Context" in detail.text
    assert expected_failure_stage in detail.text
    assert "failed" in detail.text


def test_operator_ui_created_detail_reports_partial_run_safely(tmp_path: Path) -> None:
    target_root = tmp_path / _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY
    target_root.mkdir()
    run_id = "theme_ctx_strong.analysis_failure_export.analyst_timeout"
    _write_json_only_failure_run(
        target_root,
        run_id=run_id,
        failure_stage="analyst_timeout",
    )

    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))
    response = client.get(
        f"/runs/{run_id}?created=1&target_subdirectory={_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY}"
    )

    assert response.status_code == 422
    assert "Trigger Result Unavailable" in response.text
    assert "trigger_result_unavailable" in response.text
    assert run_id in response.text
    assert _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY in response.text
    assert "artifact_markdown_missing: markdown file is missing." in response.text


def test_operator_ui_trigger_fails_safely_for_invalid_context_input(tmp_path: Path) -> None:
    missing_context_source = tmp_path / "missing.json"
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))

    response = client.post(
        "/runs/trigger",
        data={"context_source": str(missing_context_source), "analyst_mode": "stub"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "Trigger Error" in response.text
    assert "Invalid trigger input:" in response.text
    assert "context_source file does not exist." in response.text
    assert "Review Artifacts" in response.text


def test_operator_ui_reports_configured_readable_root_status(tmp_path: Path) -> None:
    _write_success_run(tmp_path)
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "Artifacts Root Status" in response.text
    assert "configured and readable" in response.text
    assert str(tmp_path.resolve()) in response.text


def test_operator_ui_run_form_shows_labels_and_help_text(tmp_path: Path) -> None:
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    body = response.text
    assert "Context Source JSON Path" in body
    assert "Target Subdirectory" in body
    assert "Analyst Mode" in body
    assert "safe default isolates UI-triggered runs" in body
    assert f"value=\"{_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY}\"" in body


def test_operator_ui_trigger_supports_explicit_target_subdirectory(tmp_path: Path) -> None:
    context_source = _write_context_source(tmp_path)
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))

    response = client.post(
        "/runs/trigger",
        data={
            "context_source": str(context_source),
            "analyst_mode": "stub",
            "target_subdirectory": "manual/session_one",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert location == (
        "/runs/theme_ctx_strong.analysis_success_export"
        "?created=1&target_subdirectory=manual%2Fsession_one"
    )

    detail = client.get(location)
    assert detail.status_code == 200
    assert "Target Subdirectory" in detail.text
    assert "manual/session_one" in detail.text

    target_root = tmp_path / "manual" / "session_one"
    assert (target_root / "theme_ctx_strong.analysis_success_export.md").exists()
    assert (target_root / "theme_ctx_strong.analysis_success_export.json").exists()


def test_operator_ui_trigger_rejects_invalid_target_subdirectory(tmp_path: Path) -> None:
    context_source = _write_context_source(tmp_path)
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))

    response = client.post(
        "/runs/trigger",
        data={
            "context_source": str(context_source),
            "analyst_mode": "stub",
            "target_subdirectory": "../escape",
        },
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "Trigger Error" in response.text
    assert "Invalid trigger input:" in response.text
    assert "target_subdirectory" in response.text


def test_operator_ui_handles_not_configured_root_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(_ARTIFACTS_ROOT_ENV, raising=False)
    client = TestClient(create_review_artifacts_operator_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "not configured" in response.text
    assert "FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT" in response.text
    assert "Triggering is unavailable" in response.text

    trigger_response = client.post(
        "/runs/trigger",
        data={"context_source": str(tmp_path / "missing.json"), "analyst_mode": "stub"},
        follow_redirects=False,
    )
    assert trigger_response.status_code == 422
    assert "artifacts_root_unavailable" in trigger_response.text


def test_operator_ui_handles_configured_but_missing_root_state(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing-root"
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=missing_root))

    response = client.get("/")

    assert response.status_code == 200
    assert "configured but missing" in response.text
    assert str(missing_root) in response.text
    assert "Triggering is unavailable" in response.text

    trigger_response = client.post(
        "/runs/trigger",
        data={"context_source": str(tmp_path / "missing.json"), "analyst_mode": "stub"},
        follow_redirects=False,
    )
    assert trigger_response.status_code == 422
    assert "artifacts_root_unavailable" in trigger_response.text

    detail_response = client.get("/runs/theme_ctx_strong.analysis_success_export")
    assert detail_response.status_code == 422
    assert "artifacts_root_unavailable" in detail_response.text


def test_operator_ui_handles_configured_but_invalid_root_state(tmp_path: Path) -> None:
    invalid_root = tmp_path / "not-a-directory"
    invalid_root.write_text("invalid", encoding="utf-8")
    client = TestClient(create_review_artifacts_operator_app(artifacts_root=invalid_root))

    response = client.get("/")

    assert response.status_code == 200
    assert "configured but unreadable/invalid" in response.text
    assert "not a directory" in response.text
    assert "Triggering is unavailable" in response.text


def test_operator_ui_handles_configured_but_unreadable_root_state(
    tmp_path: Path,
) -> None:
    artifacts_root = tmp_path / "artifacts-root"
    artifacts_root.mkdir()
    artifacts_root.chmod(0o500)
    try:
        client = TestClient(create_review_artifacts_operator_app(artifacts_root=artifacts_root))
        response = client.get("/")
        assert response.status_code == 200
        assert "configured but unreadable/invalid" in response.text
        assert "readable or unwritable" in response.text
        assert "Triggering is unavailable" in response.text
    finally:
        artifacts_root.chmod(0o700)


def _write_success_run(root: Path) -> str:
    run_id = "theme_ctx_strong.analysis_success_export"
    markdown = (
        "# Analysis Review Export\n"
        "- Export Kind: `analysis_success_export`\n"
        "- Status: `success`\n"
    )
    payload = {
        "theme_id": "theme_ctx_strong",
        "status": "success",
        "payload": {
            "export_kind": "analysis_success_export",
            "status": "success",
            "theme_id": "theme_ctx_strong",
        },
    }
    (root / f"{run_id}.md").write_text(markdown, encoding="utf-8")
    (root / f"{run_id}.json").write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return run_id


def _write_failure_run(root: Path, *, failure_stage: str) -> str:
    run_id = f"theme_ctx_strong.analysis_failure_export.{failure_stage}"
    markdown = (
        "# Analysis Review Export\n"
        "- Export Kind: `analysis_failure_export`\n"
        "- Status: `failed`\n"
        f"- Failure Stage: `{failure_stage}`\n"
    )
    payload = {
        "theme_id": "theme_ctx_strong",
        "status": "failed",
        "payload": {
            "export_kind": "analysis_failure_export",
            "status": "failed",
            "theme_id": "theme_ctx_strong",
            "failure_stage": failure_stage,
        },
    }
    (root / f"{run_id}.md").write_text(markdown, encoding="utf-8")
    (root / f"{run_id}.json").write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return run_id


def _write_json_only_failure_run(root: Path, *, run_id: str, failure_stage: str) -> None:
    payload = {
        "theme_id": "theme_ctx_strong",
        "status": "failed",
        "payload": {
            "export_kind": "analysis_failure_export",
            "status": "failed",
            "theme_id": "theme_ctx_strong",
            "failure_stage": failure_stage,
        },
    }
    (root / f"{run_id}.json").write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _write_large_run(root: Path) -> str:
    run_id = "theme_ctx_large.analysis_success_export"
    large_markdown = (
        "# Analysis Review Export\n"
        + ("- detail line for bounded display safety\n" * 900)
        + "TAIL_MARKDOWN_SENTINEL\n"
    )
    payload = {
        "theme_id": "theme_ctx_large",
        "status": "success",
        "payload": {
            "export_kind": "analysis_success_export",
            "status": "success",
            "theme_id": "theme_ctx_large",
            "large_text": ("json payload line " * 2000) + "TAIL_JSON_SENTINEL",
        },
    }
    (root / f"{run_id}.md").write_text(large_markdown, encoding="utf-8")
    (root / f"{run_id}.json").write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return run_id


def _set_mtime_ns(path: Path, *, timestamp_ns: int) -> None:
    os.utime(path, ns=(timestamp_ns, timestamp_ns))


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
