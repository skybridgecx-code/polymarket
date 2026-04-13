"""Public app-entry helpers for constructing the operator UI app."""

from __future__ import annotations

from .review_artifacts import create_review_artifacts_operator_app

# Primary operator UI app-construction entrypoint for external callers.
create_operator_ui_app = create_review_artifacts_operator_app


__all__ = [
    "create_operator_ui_app",
    "create_review_artifacts_operator_app",
]
