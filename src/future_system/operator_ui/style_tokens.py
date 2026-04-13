"""Shared styling tokens/helpers for operator UI HTML rendering."""

from __future__ import annotations

from typing import Literal

OperatorStatus = Literal["success", "failed"]

BASE_PAGE_CSS = (
    "body{font-family:ui-sans-serif,system-ui;padding:20px;background:#f8fafc;color:#111827;}"
    "a{color:#1d4ed8;text-decoration:none;}"
)
TABLE_CSS = (
    "table{border-collapse:collapse;width:100%;background:#fff;}"
    "th,td{border:1px solid #d1d5db;padding:8px;text-align:left;}"
    "th{background:#eef2ff;}"
)
BADGE_CSS = (
    ".badge{display:inline-block;padding:2px 8px;border-radius:999px;font-weight:600;}"
    ".badge-success{background:#dcfce7;color:#166534;}"
    ".badge-failed{background:#fee2e2;color:#991b1b;}"
)
ROOT_STATUS_CSS = (
    ".root-status{border:1px solid #d1d5db;padding:12px;background:#fff;margin-bottom:8px;}"
    ".root-ok{border-color:#86efac;background:#f0fdf4;}"
    ".root-problem{border-color:#fca5a5;background:#fef2f2;}"
)
FORM_CSS = (
    "input,select,button{font:inherit;padding:6px;border:1px solid #d1d5db;border-radius:4px;}"
    "label{font-weight:600;display:block;margin-bottom:4px;}"
    ".help{font-size:12px;color:#4b5563;margin-top:4px;}"
    ".form-grid{display:grid;grid-template-columns:2fr 1fr;gap:12px;max-width:920px;}"
    ".form-field{background:#fff;border:1px solid #d1d5db;padding:10px;}"
    ".form-actions{margin-top:10px;}"
)
DETAIL_SECTION_CSS = (
    ".section{margin-top:18px;background:#fff;border:1px solid #d1d5db;padding:12px;}"
    ".meta-grid{display:grid;grid-template-columns:140px 1fr;gap:6px 10px;}"
)
OUTCOME_CSS = (
    ".outcome{border-width:2px;}"
    ".outcome-success{border-color:#86efac;background:#f0fdf4;}"
    ".outcome-failed{border-color:#fca5a5;background:#fef2f2;}"
    ".outcome-label{font-size:24px;font-weight:700;margin:0 0 8px 0;}"
)
PRE_CSS = (
    "pre{white-space:pre-wrap;word-break:break-word;background:#fff;border:1px solid #d1d5db;"
    "padding:12px;max-height:540px;overflow:auto;}"
)
TRUNCATE_CSS = ".truncate{background:#fffbeb;color:#92400e;border:1px solid #fcd34d;padding:8px;}"
ERROR_CSS = ".error{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;padding:12px;}"
TERM_CSS = "dt{font-weight:600;}"

TRIGGER_ERROR_INLINE_STYLE = "color:#b91c1c;font-weight:600;"
TRIGGER_DISABLED_INLINE_STYLE = "color:#991b1b;font-weight:600;"
TRIGGER_RESULT_SECTION_INLINE_STYLE = "border-color:#86efac;background:#f0fdf4;"
TRIGGER_RESULT_HEADING_INLINE_STYLE = "color:#065f46;font-weight:600;"
TRIGGER_RESULT_NOTE_INLINE_STYLE = "margin-top:8px;color:#065f46;"


def compose_css(*fragments: str) -> str:
    """Build one deterministic style block from reusable token fragments."""

    return "".join(fragments)


def status_badge_class(status: OperatorStatus) -> str:
    """Resolve one badge class from bounded run status."""

    return "badge-success" if status == "success" else "badge-failed"


def outcome_section_class(status: OperatorStatus) -> str:
    """Resolve one outcome section class from bounded run status."""

    return "outcome-success" if status == "success" else "outcome-failed"


def outcome_label(status: OperatorStatus) -> str:
    """Resolve one deterministic outcome label from bounded run status."""

    return "SUCCESS" if status == "success" else "FAILED"


def root_status_class(*, is_usable: bool) -> str:
    """Resolve one root-status CSS class from root usability."""

    return "root-ok" if is_usable else "root-problem"


__all__ = [
    "BADGE_CSS",
    "BASE_PAGE_CSS",
    "DETAIL_SECTION_CSS",
    "ERROR_CSS",
    "FORM_CSS",
    "OUTCOME_CSS",
    "PRE_CSS",
    "ROOT_STATUS_CSS",
    "TABLE_CSS",
    "TERM_CSS",
    "TRIGGER_DISABLED_INLINE_STYLE",
    "TRIGGER_ERROR_INLINE_STYLE",
    "TRIGGER_RESULT_HEADING_INLINE_STYLE",
    "TRIGGER_RESULT_NOTE_INLINE_STYLE",
    "TRIGGER_RESULT_SECTION_INLINE_STYLE",
    "TRUNCATE_CSS",
    "compose_css",
    "outcome_label",
    "outcome_section_class",
    "root_status_class",
    "status_badge_class",
]
