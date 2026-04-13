"""Integration-style deterministic tests for operator UI read/trigger/detail and mount flows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.operator_ui import (
    DEFAULT_OPERATOR_UI_MOUNT_PATH,
    create_operator_ui_app,
    mount_operator_ui_app,
)
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_ARTIFACTS_ROOT_ENV = "FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT"
_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY = "operator_runs"


def test_create_operator_ui_app_exposes_shipped_routes(tmp_path: Path) -> None:
    app = create_operator_ui_app(artifacts_root=tmp_path)
    route_methods = _route_methods_by_path(app)

    assert route_methods["/"] == {"GET"}
    assert route_methods["/runs/trigger"] == {"POST"}
    assert route_methods["/runs/{run_id}"] == {"GET"}


def test_mount_operator_ui_app_default_path_serves_operator_ui(tmp_path: Path) -> None:
    parent_app = FastAPI()
    mount_operator_ui_app(parent_app=parent_app, artifacts_root=tmp_path)

    client = TestClient(parent_app)
    response = client.get(f"{DEFAULT_OPERATOR_UI_MOUNT_PATH}/")

    assert response.status_code == 200
    assert "Review Artifacts" in response.text


def test_get_root_renders_configured_readable_list_state(tmp_path: Path) -> None:
    run_id = _write_success_run(tmp_path)
    client = TestClient(create_operator_ui_app(artifacts_root=tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "configured and readable" in response.text
    assert run_id in response.text
    assert "SUCCESS" in response.text


def test_trigger_success_redirects_and_hands_off_to_detail_with_default_subdirectory(
    tmp_path: Path,
) -> None:
    context_source = _write_context_source(tmp_path)
    client = TestClient(create_operator_ui_app(artifacts_root=tmp_path))

    trigger = client.post(
        "/runs/trigger",
        data={"context_source": str(context_source), "analyst_mode": "stub"},
        follow_redirects=False,
    )

    assert trigger.status_code == 303
    location = trigger.headers["location"]
    assert location.startswith("/runs/theme_ctx_strong.analysis_success_export?")
    assert f"target_subdirectory={_DEFAULT_TRIGGER_TARGET_SUBDIRECTORY}" in location

    detail = client.get(location)
    assert detail.status_code == 200
    assert "Review Artifact Detail" in detail.text
    assert "Run created via trigger and loaded." in detail.text
    assert _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY in detail.text

    target_root = tmp_path / _DEFAULT_TRIGGER_TARGET_SUBDIRECTORY
    assert (target_root / "theme_ctx_strong.analysis_success_export.md").exists()
    assert (target_root / "theme_ctx_strong.analysis_success_export.json").exists()


def test_detail_view_preserves_success_and_failure_stage_visibility(tmp_path: Path) -> None:
    success_run_id = _write_success_run(tmp_path)
    failure_run_id = _write_failure_run(tmp_path, failure_stage="analyst_transport")
    client = TestClient(create_operator_ui_app(artifacts_root=tmp_path))

    success_response = client.get(f"/runs/{success_run_id}")
    failure_response = client.get(f"/runs/{failure_run_id}")

    assert success_response.status_code == 200
    assert "SUCCESS" in success_response.text
    assert "Failure Stage</dt><dd>none" in success_response.text

    assert failure_response.status_code == 200
    assert "FAILED (analyst_transport)" in failure_response.text
    assert "analyst_transport" in failure_response.text


def test_triggered_runs_in_operator_runs_are_not_auto_listed_at_root(tmp_path: Path) -> None:
    context_source = _write_context_source(tmp_path)
    client = TestClient(create_operator_ui_app(artifacts_root=tmp_path))

    trigger = client.post(
        "/runs/trigger",
        data={"context_source": str(context_source), "analyst_mode": "stub"},
        follow_redirects=False,
    )
    assert trigger.status_code == 303
    triggered_run_id = trigger.headers["location"].split("/runs/", 1)[1].split("?", 1)[0]

    root_list = client.get("/")
    assert root_list.status_code == 200
    assert "No runs found." in root_list.text
    assert triggered_run_id not in root_list.text

    root_run_id = _write_failure_run(tmp_path, failure_stage="reasoning_parse")
    refreshed_list = client.get("/")
    assert refreshed_list.status_code == 200
    assert root_run_id in refreshed_list.text
    assert triggered_run_id not in refreshed_list.text


def test_root_status_messages_are_bounded_for_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(_ARTIFACTS_ROOT_ENV, raising=False)
    client = TestClient(create_operator_ui_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "not configured" in response.text
    assert _ARTIFACTS_ROOT_ENV in response.text
    assert "Triggering is unavailable" in response.text


def test_root_status_messages_are_bounded_for_missing_and_invalid(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing-root"
    missing_client = TestClient(create_operator_ui_app(artifacts_root=missing_root))
    missing_response = missing_client.get("/")
    assert missing_response.status_code == 200
    assert "configured but missing" in missing_response.text
    assert "Triggering is unavailable" in missing_response.text

    invalid_root = tmp_path / "not-a-directory"
    invalid_root.write_text("invalid", encoding="utf-8")
    invalid_client = TestClient(create_operator_ui_app(artifacts_root=invalid_root))
    invalid_response = invalid_client.get("/")
    assert invalid_response.status_code == 200
    assert "configured but unreadable/invalid" in invalid_response.text
    assert "not a directory" in invalid_response.text
    assert "Triggering is unavailable" in invalid_response.text


def _route_methods_by_path(app: FastAPI) -> dict[str, set[str]]:
    route_methods: dict[str, set[str]] = {}
    for route in app.routes:
        route_path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if not isinstance(route_path, str) or not isinstance(methods, set):
            continue
        route_methods[route_path] = set(methods) - {"HEAD", "OPTIONS"}
    return route_methods


def _write_success_run(root: Path) -> str:
    run_id = "theme_ctx_strong.integration_success_export"
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
    run_id = f"theme_ctx_strong.integration_failure_export.{failure_stage}"
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
