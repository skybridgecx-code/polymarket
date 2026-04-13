"""Deterministic tests for future_system.operator_ui.review_artifacts read-only screen."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from future_system.operator_ui.review_artifacts import create_review_artifacts_operator_app


def test_operator_ui_lists_success_and_failure_runs_with_stage_context(tmp_path: Path) -> None:
    _write_success_run(tmp_path)
    _write_failure_run(tmp_path, failure_stage="analyst_transport")

    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))
    response = client.get("/")

    assert response.status_code == 200
    body = response.text
    assert "Review Artifacts" in body
    assert "theme_ctx_strong.analysis_success_export" in body
    assert "theme_ctx_strong.analysis_failure_export.analyst_transport" in body
    assert "success" in body
    assert "failed" in body
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


def test_operator_ui_detail_fails_safely_when_markdown_is_missing(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_failure_export.analyst_timeout"
    _write_json_only_failure_run(tmp_path, run_id=run_id, failure_stage="analyst_timeout")

    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))
    response = client.get(f"/runs/{run_id}")

    assert response.status_code == 422
    assert response.json()["detail"] == "artifact_markdown_missing: markdown file is missing."


def test_operator_ui_detail_fails_safely_for_invalid_json(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    (tmp_path / f"{run_id}.md").write_text("# Analysis Review Export\n", encoding="utf-8")
    (tmp_path / f"{run_id}.json").write_text("{invalid_json", encoding="utf-8")

    client = TestClient(create_review_artifacts_operator_app(artifacts_root=tmp_path))
    response = client.get(f"/runs/{run_id}")

    assert response.status_code == 422
    assert response.json()["detail"] == "artifact_json_invalid: malformed JSON content."


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
