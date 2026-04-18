from __future__ import annotations

import json
from pathlib import Path

from future_system.operator_review_models.models import OperatorReviewDecisionRecord
from future_system.review_outcome_packaging.models import (
    ReviewOutcomePackage,
    ReviewOutcomePackagePaths,
    ReviewOutcomePackagePayload,
    package_dir_for_run,
)


def _read_json_dict(*, path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing_required_file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_json_file: {path}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"invalid_json_object: {path}")
    return payload


def build_review_outcome_package(
    *,
    run_id: str,
    markdown_artifact_path: Path,
    json_artifact_path: Path,
    operator_review_metadata_path: Path,
    target_root: Path,
) -> ReviewOutcomePackage:
    if not markdown_artifact_path.is_file():
        raise ValueError(f"missing_markdown_artifact: {markdown_artifact_path}")
    if not json_artifact_path.is_file():
        raise ValueError(f"missing_json_artifact: {json_artifact_path}")
    if not operator_review_metadata_path.is_file():
        raise ValueError(
            f"missing_operator_review_metadata: {operator_review_metadata_path}"
        )

    _read_json_dict(path=json_artifact_path)
    review_payload = _read_json_dict(path=operator_review_metadata_path)

    record = OperatorReviewDecisionRecord.model_validate(review_payload)

    artifact_ref = review_payload.get("artifact")
    if not isinstance(artifact_ref, dict):
        raise ValueError("invalid_operator_review_metadata: missing artifact block")

    review_run_id = artifact_ref.get("run_id")
    if review_run_id != run_id:
        raise ValueError("invalid_operator_review_metadata: run_id mismatch")

    run_status = artifact_ref.get("status")
    export_kind = artifact_ref.get("export_kind")
    if not isinstance(run_status, str) or not isinstance(export_kind, str):
        raise ValueError("invalid_operator_review_metadata: missing artifact status")

    package_dir = package_dir_for_run(target_root=target_root, run_id=run_id)
    summary_path = package_dir / "handoff_summary.md"
    payload_path = package_dir / "handoff_payload.json"

    payload = ReviewOutcomePackagePayload(
        run_id=run_id,
        run_status=run_status,
        export_kind=export_kind,
        markdown_artifact_path=str(markdown_artifact_path),
        json_artifact_path=str(json_artifact_path),
        operator_review_metadata_path=str(operator_review_metadata_path),
        review_status=record.review_status,
        operator_decision=record.operator_decision,
        review_notes_summary=record.review_notes_summary,
        reviewer_identity=record.reviewer_identity,
    )
    paths = ReviewOutcomePackagePaths(
        package_dir=str(package_dir),
        handoff_summary_path=str(summary_path),
        handoff_payload_path=str(payload_path),
    )
    return ReviewOutcomePackage(payload=payload, paths=paths)


def render_review_outcome_handoff_markdown(
    *, package: ReviewOutcomePackage
) -> str:
    p = package.payload
    return "\n".join(
        [
            f"# Review Outcome Handoff — {p.run_id}",
            "",
            "## Run",
            f"- Run ID: `{p.run_id}`",
            f"- Status: `{p.run_status}`",
            f"- Export Kind: `{p.export_kind}`",
            "",
            "## Artifact Paths",
            f"- Markdown Artifact: `{p.markdown_artifact_path}`",
            f"- JSON Artifact: `{p.json_artifact_path}`",
            f"- Decision Metadata: `{p.operator_review_metadata_path}`",
            "",
            "## Operator Review Outcome",
            f"- Review Status: `{p.review_status}`",
            f"- Operator Decision: `{p.operator_decision or 'none'}`",
            f"- Review Notes Summary: `{p.review_notes_summary or 'none'}`",
            f"- Reviewer Identity: `{p.reviewer_identity or 'none'}`",
            "",
            "## Local Note",
            "- This package is a deterministic local review outcome artifact.",
            "- It does not upload or deliver anything externally.",
            "",
        ]
    )
