"""Public app-entry helpers for constructing the operator UI app."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from .review_artifacts import create_review_artifacts_operator_app

# Primary operator UI app-construction entrypoint for external callers.
create_operator_ui_app = create_review_artifacts_operator_app
DEFAULT_OPERATOR_UI_MOUNT_PATH = "/operator-ui"


def mount_operator_ui_app(
    *,
    parent_app: FastAPI,
    artifacts_root: str | Path | None = None,
    mount_path: str = DEFAULT_OPERATOR_UI_MOUNT_PATH,
) -> FastAPI:
    """Mount the operator UI app into a parent FastAPI app at one normalized path."""

    normalized_mount_path = _normalize_mount_path(mount_path)
    parent_app.mount(
        normalized_mount_path,
        create_operator_ui_app(artifacts_root=artifacts_root),
    )
    return parent_app


def _normalize_mount_path(mount_path: str) -> str:
    normalized = mount_path.strip()
    if not normalized:
        raise ValueError("mount_path must be a non-empty absolute path.")
    if not normalized.startswith("/"):
        raise ValueError("mount_path must start with '/'.")
    if len(normalized) > 1 and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized


__all__ = [
    "DEFAULT_OPERATOR_UI_MOUNT_PATH",
    "create_operator_ui_app",
    "create_review_artifacts_operator_app",
    "mount_operator_ui_app",
]
