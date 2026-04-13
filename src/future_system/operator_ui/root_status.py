"""Bounded artifacts-root status helpers for the operator UI surface."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ARTIFACTS_ROOT_ENV = "FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT"


@dataclass(frozen=True)
class ArtifactsRootStatus:
    """Bounded status for configured artifacts root visibility and safety checks."""

    state: Literal[
        "configured_readable",
        "configured_missing",
        "configured_invalid_or_unreadable",
        "not_configured",
    ]
    configured_value: str | None
    resolved_root: Path | None
    message: str

    @property
    def is_usable(self) -> bool:
        return self.state == "configured_readable" and self.resolved_root is not None


def resolve_artifacts_root(artifacts_root: str | Path | None) -> Path:
    """Resolve one usable artifacts root path or raise a safe bounded error."""

    status = resolve_artifacts_root_status(artifacts_root)
    if status.is_usable and status.resolved_root is not None:
        return status.resolved_root
    raise ValueError(artifacts_root_unavailable_message(root_status=status))


def resolve_artifacts_root_status(artifacts_root: str | Path | None) -> ArtifactsRootStatus:
    """Resolve artifacts root into one explicit deterministic operator-safe status."""

    configured_value: str | None = None
    candidate: Path | None = None

    if artifacts_root is None:
        env_value = os.getenv(ARTIFACTS_ROOT_ENV, "").strip()
        if not env_value:
            return ArtifactsRootStatus(
                state="not_configured",
                configured_value=None,
                resolved_root=None,
                message=(
                    "Artifacts root is not configured. Set "
                    f"{ARTIFACTS_ROOT_ENV} or pass artifacts_root when creating the app."
                ),
            )
        configured_value = env_value
        candidate = Path(env_value)
    elif isinstance(artifacts_root, Path):
        configured_value = str(artifacts_root)
        candidate = artifacts_root
    elif isinstance(artifacts_root, str):
        stripped = artifacts_root.strip()
        if not stripped:
            return ArtifactsRootStatus(
                state="configured_invalid_or_unreadable",
                configured_value=artifacts_root,
                resolved_root=None,
                message="Configured artifacts root is invalid: path string is empty.",
            )
        configured_value = stripped
        candidate = Path(stripped)
    else:
        raise ValueError("artifacts_root must be a path-like string or Path.")

    assert candidate is not None
    try:
        resolved_candidate = candidate.resolve(strict=False)
    except OSError:
        return ArtifactsRootStatus(
            state="configured_invalid_or_unreadable",
            configured_value=configured_value,
            resolved_root=None,
            message="Configured artifacts root is unreadable or invalid.",
        )

    if not resolved_candidate.exists():
        return ArtifactsRootStatus(
            state="configured_missing",
            configured_value=configured_value,
            resolved_root=None,
            message="Configured artifacts root is missing on disk.",
        )
    if not resolved_candidate.is_dir():
        return ArtifactsRootStatus(
            state="configured_invalid_or_unreadable",
            configured_value=configured_value,
            resolved_root=None,
            message="Configured artifacts root is invalid: path is not a directory.",
        )

    required_access = os.R_OK | os.W_OK | os.X_OK
    if not os.access(resolved_candidate, required_access):
        return ArtifactsRootStatus(
            state="configured_invalid_or_unreadable",
            configured_value=configured_value,
            resolved_root=None,
            message=(
                "Configured artifacts root is unreadable or unwritable; read/write access "
                "is required."
            ),
        )

    return ArtifactsRootStatus(
        state="configured_readable",
        configured_value=str(resolved_candidate),
        resolved_root=resolved_candidate,
        message="Configured artifacts root is readable and writable.",
    )


def artifacts_root_unavailable_message(*, root_status: ArtifactsRootStatus) -> str:
    """Render one bounded unavailable-root message consistent with current UI behavior."""

    if root_status.state == "not_configured":
        return f"artifacts_root is required unless {ARTIFACTS_ROOT_ENV} is configured."
    if root_status.state == "configured_missing":
        return "artifacts_root must reference an existing directory."
    return "artifacts_root must reference a readable and writable directory."


__all__ = [
    "ARTIFACTS_ROOT_ENV",
    "ArtifactsRootStatus",
    "artifacts_root_unavailable_message",
    "resolve_artifacts_root",
    "resolve_artifacts_root_status",
]
