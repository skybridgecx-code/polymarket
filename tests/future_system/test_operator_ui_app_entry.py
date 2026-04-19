"""Deterministic tests for operator_ui app-entry launch/mount helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from future_system.operator_ui import (
    DEFAULT_OPERATOR_UI_MOUNT_PATH,
    mount_operator_ui_app,
)


def test_mount_operator_ui_app_uses_default_mount_path(tmp_path: Path) -> None:
    parent_app = FastAPI()
    mounted_app = mount_operator_ui_app(
        parent_app=parent_app,
        artifacts_root=tmp_path,
    )

    assert mounted_app is parent_app
    client = TestClient(parent_app)
    response = client.get(f"{DEFAULT_OPERATOR_UI_MOUNT_PATH}/")

    assert response.status_code == 200
    assert "Local Review Runs" in response.text


def test_mount_operator_ui_app_supports_custom_mount_path(tmp_path: Path) -> None:
    parent_app = FastAPI()
    mount_operator_ui_app(
        parent_app=parent_app,
        artifacts_root=tmp_path,
        mount_path="/ops/review-console/",
    )

    client = TestClient(parent_app)
    response = client.get("/ops/review-console/")

    assert response.status_code == 200
    assert "Local Review Runs" in response.text


def test_mount_operator_ui_app_rejects_invalid_mount_path(tmp_path: Path) -> None:
    parent_app = FastAPI()

    with pytest.raises(ValueError, match="mount_path"):
        mount_operator_ui_app(
            parent_app=parent_app,
            artifacts_root=tmp_path,
            mount_path="operator-ui",
        )
