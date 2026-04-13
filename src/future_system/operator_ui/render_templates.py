"""HTML rendering helpers for the operator UI review artifacts surface."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Literal

from future_system.runtime.models import AnalysisRunFailureStage

from .artifact_reads import (
    ArtifactRunDetail,
    ArtifactRunHistory,
    status_label,
)
from .root_status import ARTIFACTS_ROOT_ENV, ArtifactsRootStatus
from .style_tokens import (
    BADGE_CSS,
    BASE_PAGE_CSS,
    DETAIL_SECTION_CSS,
    ERROR_CSS,
    FORM_CSS,
    OUTCOME_CSS,
    PRE_CSS,
    ROOT_STATUS_CSS,
    TABLE_CSS,
    TERM_CSS,
    TRIGGER_DISABLED_INLINE_STYLE,
    TRIGGER_ERROR_INLINE_STYLE,
    TRIGGER_RESULT_HEADING_INLINE_STYLE,
    TRIGGER_RESULT_NOTE_INLINE_STYLE,
    TRIGGER_RESULT_SECTION_INLINE_STYLE,
    TRUNCATE_CSS,
    compose_css,
    outcome_label,
    outcome_section_class,
    root_status_class,
    status_badge_class,
)

DETAIL_MARKDOWN_MAX_CHARS = 16_000
DETAIL_JSON_MAX_CHARS = 24_000
LIST_PAGE_CSS = compose_css(
    BASE_PAGE_CSS,
    TABLE_CSS,
    BADGE_CSS,
    ROOT_STATUS_CSS,
    FORM_CSS,
)
DETAIL_PAGE_CSS = compose_css(
    BASE_PAGE_CSS,
    BADGE_CSS,
    DETAIL_SECTION_CSS,
    OUTCOME_CSS,
    PRE_CSS,
    TERM_CSS,
    TRUNCATE_CSS,
)
ERROR_PAGE_CSS = compose_css(
    BASE_PAGE_CSS,
    ERROR_CSS,
)
FAILURE_STAGE_DESCRIPTIONS: dict[AnalysisRunFailureStage, str] = {
    "analyst_timeout": "Analyst timed out before producing a complete response.",
    "analyst_transport": "Analyst transport call failed before a usable response was returned.",
    "reasoning_parse": "Analyst response was received but reasoning payload parsing failed.",
}


def render_list_page(
    *,
    history: ArtifactRunHistory,
    root_status: ArtifactsRootStatus,
    trigger_error: str | None,
    last_context_source: str,
    last_analyst_mode: str,
    last_target_subdirectory: str,
    trigger_analyst_mode_choices: tuple[str, ...],
) -> str:
    """Render list/trigger page HTML from deterministic history and root-state inputs."""

    rows: list[str] = []
    for run in history.runs:
        status_badge = _render_status_badge(status=run.status, failure_stage=run.failure_stage)
        failure_stage = run.failure_stage if run.failure_stage is not None else "none"
        rows.append(
            "<tr>"
            f"<td><a href=\"/runs/{html.escape(run.run_id)}\">{html.escape(run.run_id)}</a></td>"
            f"<td>{html.escape(run.theme_id)}</td>"
            f"<td>{status_badge}</td>"
            f"<td>{html.escape(failure_stage)}</td>"
            f"<td>{html.escape(run.updated_at_label)}</td>"
            "</tr>"
        )

    table_rows = "".join(rows) if rows else "<tr><td colspan=\"5\">No runs found.</td></tr>"
    error_block = ""
    if trigger_error is not None:
        error_block = (
            f"<p style=\"{TRIGGER_ERROR_INLINE_STYLE}\">Trigger Error: "
            f"{html.escape(trigger_error)}</p>"
        )
    issue_rows: list[str] = []
    for issue in history.issues:
        issue_rows.append(
            "<tr>"
            f"<td>{html.escape(issue.run_id)}</td>"
            f"<td>{html.escape(issue.issue_kind)}</td>"
            f"<td>{html.escape(issue.issue_message)}</td>"
            f"<td>{html.escape(issue.json_path)}</td>"
            "</tr>"
        )
    issues_block = ""
    if issue_rows:
        issues_block = (
            "<h2>Run Issues</h2>"
            "<p>Some run files are incomplete or invalid and were safely skipped from details.</p>"
            "<table><thead><tr><th>Run</th><th>Issue</th><th>Message</th><th>JSON Path</th>"
            f"</tr></thead><tbody>{''.join(issue_rows)}</tbody></table>"
        )

    selected_mode = (
        last_analyst_mode if last_analyst_mode in trigger_analyst_mode_choices else "stub"
    )
    mode_options: list[str] = []
    for mode in trigger_analyst_mode_choices:
        selected_attr = " selected" if mode == selected_mode else ""
        mode_options.append(
            f"<option value=\"{html.escape(mode)}\"{selected_attr}>{html.escape(mode)}</option>"
        )
    mode_options_html = "".join(mode_options)
    root_status_label = _render_artifacts_root_state_label(root_status=root_status)
    root_status_css_class = root_status_class(is_usable=root_status.is_usable)
    configured_value = (
        html.escape(root_status.configured_value)
        if root_status.configured_value is not None
        else f"(unset; {ARTIFACTS_ROOT_ENV} is empty)"
    )
    root_message_html = html.escape(root_status.message)
    root_block = (
        "<h2>Artifacts Root Status</h2>"
        f"<div class=\"root-status {root_status_css_class}\">"
        f"<p><strong>Status:</strong> {html.escape(root_status_label)}</p>"
        f"<p><strong>Configured Value:</strong> <code>{configured_value}</code></p>"
        f"<p>{root_message_html}</p>"
        "</div>"
    )
    disable_trigger_attr = " disabled" if not root_status.is_usable else ""
    trigger_disabled_block = ""
    if not root_status.is_usable:
        trigger_disabled_block = (
            f"<p style=\"{TRIGGER_DISABLED_INLINE_STYLE}\">"
            "Triggering is unavailable until artifacts root configuration is fixed."
            "</p>"
        )
    context_source_input = html.escape(last_context_source)
    target_subdirectory_input = html.escape(last_target_subdirectory.strip())

    return (
        "<!doctype html>"
        "<html><head><meta charset=\"utf-8\"><title>Review Artifacts</title>"
        f"<style>{LIST_PAGE_CSS}</style></head><body>"
        "<h1>Review Artifacts</h1>"
        f"{root_block}"
        "<h2>Trigger Run</h2>"
        "<form action=\"/runs/trigger\" method=\"post\">"
        "<div class=\"form-grid\">"
        "<div class=\"form-field\">"
        "<label for=\"context_source\">Context Source JSON Path</label>"
        "<input id=\"context_source\" type=\"text\" name=\"context_source\" "
        "placeholder=\"/absolute/path/context_bundle.json\" "
        f"value=\"{context_source_input}\" required{disable_trigger_attr}>"
        "<p class=\"help\">Provide an existing OpportunityContextBundle JSON file path.</p>"
        "</div>"
        "<div class=\"form-field\">"
        "<label for=\"target_subdirectory\">Target Subdirectory</label>"
        "<input id=\"target_subdirectory\" type=\"text\" name=\"target_subdirectory\" "
        f"value=\"{target_subdirectory_input}\" required{disable_trigger_attr}>"
        "<p class=\"help\">Relative subdirectory under artifacts root; "
        "safe default isolates UI-triggered runs.</p>"
        "</div>"
        "<div class=\"form-field\">"
        "<label for=\"analyst_mode\">Analyst Mode</label>"
        f"<select id=\"analyst_mode\" name=\"analyst_mode\"{disable_trigger_attr}>"
        f"{mode_options_html}</select>"
        "<p class=\"help\">Use `stub` for normal deterministic success or choose "
        "a failure mode.</p>"
        "</div>"
        "</div>"
        "<div class=\"form-actions\">"
        f"<button type=\"submit\"{disable_trigger_attr}>Run Analysis</button>"
        "</div>"
        "</form>"
        f"{trigger_disabled_block}"
        f"{error_block}"
        "<h2>Runs</h2>"
        "<table><thead><tr>"
        "<th>Run</th><th>Theme ID</th><th>Status</th><th>Failure Stage</th><th>Updated</th>"
        f"</tr></thead><tbody>{table_rows}</tbody></table>"
        f"{issues_block}"
        "</body></html>"
    )


def render_detail_page(
    *,
    detail: ArtifactRunDetail,
    created_via_trigger: bool,
    target_subdirectory: str | None,
) -> str:
    """Render detail page HTML from one deterministic run detail payload."""

    failure_stage = detail.run.failure_stage if detail.run.failure_stage is not None else "none"
    status_badge = _render_status_badge(
        status=detail.run.status,
        failure_stage=detail.run.failure_stage,
    )
    outcome_label_text = outcome_label(detail.run.status)
    outcome_tone_class = outcome_section_class(detail.run.status)
    failure_stage_description = _failure_stage_description(
        status=detail.run.status,
        failure_stage=detail.run.failure_stage,
    )
    artifact_directory = str(Path(detail.run.json_path).parent)
    target_subdirectory_display = (
        target_subdirectory if target_subdirectory is not None else "(not provided)"
    )
    markdown_display, markdown_truncated, markdown_total_chars = _bounded_display_text(
        detail.markdown_content,
        max_chars=DETAIL_MARKDOWN_MAX_CHARS,
    )
    json_pretty = json.dumps(detail.json_content, indent=2, sort_keys=True)
    json_display, json_truncated, json_total_chars = _bounded_display_text(
        json_pretty,
        max_chars=DETAIL_JSON_MAX_CHARS,
    )
    markdown_block = html.escape(markdown_display)
    json_block = html.escape(json_display)
    markdown_notice = ""
    if markdown_truncated:
        markdown_notice = (
            "<p class=\"truncate\">Markdown content display truncated for safety: "
            f"showing first {DETAIL_MARKDOWN_MAX_CHARS} of {markdown_total_chars} characters.</p>"
        )
    json_notice = ""
    if json_truncated:
        json_notice = (
            "<p class=\"truncate\">JSON content display truncated for safety: "
            f"showing first {DETAIL_JSON_MAX_CHARS} of {json_total_chars} characters.</p>"
        )
    created_block = ""
    if created_via_trigger:
        created_block = (
            f"<section class=\"section\" style=\"{TRIGGER_RESULT_SECTION_INLINE_STYLE}\">"
            "<h2>Trigger Result Summary</h2>"
            f"<p style=\"{TRIGGER_RESULT_HEADING_INLINE_STYLE}\">"
            "Run created via trigger and loaded.</p>"
            "<dl class=\"meta-grid\">"
            f"<dt>Run ID</dt><dd>{html.escape(detail.run.run_id)}</dd>"
            f"<dt>Theme ID</dt><dd>{html.escape(detail.run.theme_id)}</dd>"
            f"<dt>Run Outcome</dt><dd>{status_badge}</dd>"
            f"<dt>Failure Stage</dt><dd>{html.escape(failure_stage)}</dd>"
            f"<dt>Target Subdirectory</dt><dd>{html.escape(target_subdirectory_display)}</dd>"
            f"<dt>Artifact Directory</dt><dd>{html.escape(artifact_directory)}</dd>"
            "</dl>"
            f"<p style=\"{TRIGGER_RESULT_NOTE_INLINE_STYLE}\">"
            "Inspect outcome and artifact content "
            "sections below for full details.</p>"
            "</section>"
        )

    return (
        "<!doctype html>"
        "<html><head><meta charset=\"utf-8\"><title>Review Artifact Detail</title>"
        f"<style>{DETAIL_PAGE_CSS}</style></head><body>"
        "<p><a href=\"/\">Back to runs</a></p>"
        f"{created_block}"
        "<h1>Review Artifact Detail</h1>"
        f"<section class=\"section outcome {outcome_tone_class}\">"
        "<h2>Outcome Summary</h2>"
        f"<p class=\"outcome-label\">{html.escape(outcome_label_text)}</p>"
        "<dl class=\"meta-grid\">"
        f"<dt>Status Label</dt><dd>{html.escape(detail.run.status_label)}</dd>"
        f"<dt>Failure Stage</dt><dd>{html.escape(failure_stage)}</dd>"
        f"<dt>Failure Context</dt><dd>{html.escape(failure_stage_description)}</dd>"
        "</dl>"
        "</section>"
        "<section class=\"section\">"
        "<h2>Run Metadata</h2>"
        "<dl class=\"meta-grid\">"
        f"<dt>Run</dt><dd>{html.escape(detail.run.run_id)}</dd>"
        f"<dt>Theme ID</dt><dd>{html.escape(detail.run.theme_id)}</dd>"
        f"<dt>Status</dt><dd>{status_badge}</dd>"
        f"<dt>Failure Stage</dt><dd>{html.escape(failure_stage)}</dd>"
        f"<dt>Updated</dt><dd>{html.escape(detail.run.updated_at_label)}</dd>"
        "</dl>"
        "</section>"
        "<section class=\"section\">"
        "<h2>Artifact Paths</h2>"
        "<dl class=\"meta-grid\">"
        f"<dt>Target Subdirectory</dt><dd>{html.escape(target_subdirectory_display)}</dd>"
        f"<dt>Artifact Directory</dt><dd>{html.escape(artifact_directory)}</dd>"
        f"<dt>Markdown Path</dt><dd>{html.escape(detail.run.markdown_path)}</dd>"
        f"<dt>JSON Path</dt><dd>{html.escape(detail.run.json_path)}</dd>"
        f"<dt>Markdown Size</dt><dd>{len(detail.markdown_content)} chars</dd>"
        f"<dt>JSON Size</dt><dd>{len(json_pretty)} chars</dd>"
        "</dl>"
        "</section>"
        "<section class=\"section\">"
        "<h2>Artifact Content</h2>"
        "<h3>Markdown Content</h3>"
        f"{markdown_notice}"
        f"<pre>{markdown_block}</pre>"
        "<h3>JSON Content</h3>"
        f"{json_notice}"
        f"<pre>{json_block}</pre>"
        "</section>"
        "</body></html>"
    )


def render_error_page(*, title: str, message: str, back_href: str, back_label: str) -> str:
    """Render one bounded operator-safe HTML error page."""

    return (
        "<!doctype html>"
        f"<html><head><meta charset=\"utf-8\"><title>{html.escape(title)}</title>"
        f"<style>{ERROR_PAGE_CSS}</style></head><body>"
        f"<p><a href=\"{html.escape(back_href)}\">{html.escape(back_label)}</a></p>"
        f"<h1>{html.escape(title)}</h1>"
        f"<div class=\"error\">{html.escape(message)}</div>"
        "</body></html>"
    )


def _render_artifacts_root_state_label(*, root_status: ArtifactsRootStatus) -> str:
    if root_status.state == "configured_readable":
        return "configured and readable"
    if root_status.state == "configured_missing":
        return "configured but missing"
    if root_status.state == "configured_invalid_or_unreadable":
        return "configured but unreadable/invalid"
    return "not configured"


def _render_status_badge(
    *,
    status: Literal["success", "failed"],
    failure_stage: AnalysisRunFailureStage | None,
) -> str:
    label = status_label(status=status, failure_stage=failure_stage)
    class_name = status_badge_class(status)
    return f"<span class=\"badge {class_name}\">{html.escape(label)}</span>"


def _bounded_display_text(value: str, *, max_chars: int) -> tuple[str, bool, int]:
    total_chars = len(value)
    if total_chars <= max_chars:
        return value, False, total_chars
    return value[:max_chars], True, total_chars


def _failure_stage_description(
    *,
    status: Literal["success", "failed"],
    failure_stage: AnalysisRunFailureStage | None,
) -> str:
    if status == "success":
        return "No failure stage. Run completed successfully."
    if failure_stage is None:
        return "Failure stage is unavailable for this failed run."
    return FAILURE_STAGE_DESCRIPTIONS[failure_stage]


__all__ = [
    "render_detail_page",
    "render_error_page",
    "render_list_page",
]
