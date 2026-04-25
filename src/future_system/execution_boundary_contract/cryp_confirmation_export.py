"""Export reviewed Polymarket signals as cryp external confirmation artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from future_system.cryp_external_confirmation_signal import (
    SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSET_MAP,
    ReviewedPolymarketExternalConfirmationSignal,
)
from future_system.operator_review_models.models import OperatorReviewDecisionRecord
from future_system.review_outcome_packaging.models import ReviewOutcomePackagePayload

_SOURCE_SIGNAL_KEY = "cryp_external_confirmation_signal"


class CrypExternalConfirmationArtifact(BaseModel):
    """Exact JSON shape consumed by cryp external confirmation ingestion."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: Literal["external_confirmation_advisory_v1"] = (
        "external_confirmation_advisory_v1"
    )
    asset: str = Field(min_length=1)
    directional_bias: Literal["buy", "sell", "neutral"]
    confidence_adjustment: float = Field(ge=-0.5, le=0.5)
    rationale: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    supporting_tags: list[str] = Field(default_factory=list)
    veto_trade: bool
    correlation_id: str | None = None
    observed_at_epoch_ns: int = Field(ge=0)

    @field_validator("asset", "rationale", "source_system", mode="before")
    @classmethod
    def _normalize_required_text(cls, value: Any, info: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{info.field_name}_must_be_string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{info.field_name}_must_be_non_empty")
        return normalized

    @field_validator("supporting_tags", mode="before")
    @classmethod
    def _normalize_supporting_tags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("supporting_tags_must_be_list")
        normalized: list[str] = []
        for raw in value:
            if not isinstance(raw, str):
                raise ValueError("supporting_tags_must_be_string")
            token = raw.strip()
            if not token or token in normalized:
                continue
            normalized.append(token)
        return normalized


class CrypExternalConfirmationExportResult(BaseModel):
    """Operator-visible result for one exported cryp advisory artifact."""

    model_config = ConfigDict(extra="forbid")

    result_kind: Literal["cryp_external_confirmation_export_result"] = (
        "cryp_external_confirmation_export_result"
    )
    status: Literal["exported"]
    package_dir: str
    source_json_artifact_path: str
    output_path: str
    asset: str
    directional_bias: Literal["buy", "sell", "neutral"]
    veto_trade: bool
    correlation_id: str | None


def build_cryp_external_confirmation_artifact_from_package(
    *, package_dir: Path
) -> CrypExternalConfirmationArtifact:
    """Build one cryp-consumable advisory artifact from a reviewed package."""

    resolved_package_dir = package_dir.resolve()
    handoff_payload = _load_handoff_payload(package_dir=resolved_package_dir)
    operator_review = _load_operator_review(handoff_payload=handoff_payload)
    _validate_reviewed_approved_package(
        handoff_payload=handoff_payload,
        operator_review=operator_review,
    )
    signal = _load_reviewed_signal(handoff_payload=handoff_payload)

    directional_bias, veto_trade = _map_signal_to_cryp_bias(signal.signal)
    observed_at_epoch_ns = (
        signal.observed_at_epoch_ns
        or operator_review.updated_at_epoch_ns
        or operator_review.decided_at_epoch_ns
    )
    if observed_at_epoch_ns is None:
        raise ValueError("cryp_confirmation_export_missing_observed_at_epoch_ns")

    return CrypExternalConfirmationArtifact(
        asset=SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSET_MAP[signal.asset],
        directional_bias=directional_bias,
        confidence_adjustment=signal.confidence_adjustment,
        rationale=signal.rationale,
        source_system=signal.source_system,
        supporting_tags=signal.supporting_tags,
        veto_trade=veto_trade,
        correlation_id=signal.correlation_id or handoff_payload.run_id,
        observed_at_epoch_ns=observed_at_epoch_ns,
    )


def write_cryp_external_confirmation_artifact_from_package(
    *,
    package_dir: Path,
    output_path: Path,
) -> CrypExternalConfirmationExportResult:
    """Write one cryp-consumable advisory artifact from a reviewed package."""

    resolved_package_dir = package_dir.resolve()
    handoff_payload = _load_handoff_payload(package_dir=resolved_package_dir)
    artifact = build_cryp_external_confirmation_artifact_from_package(
        package_dir=resolved_package_dir
    )
    resolved_output_path = output_path.resolve()
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(
        f"{json.dumps(artifact.model_dump(mode='json'), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return CrypExternalConfirmationExportResult(
        status="exported",
        package_dir=str(resolved_package_dir),
        source_json_artifact_path=handoff_payload.json_artifact_path,
        output_path=str(resolved_output_path),
        asset=artifact.asset,
        directional_bias=artifact.directional_bias,
        veto_trade=artifact.veto_trade,
        correlation_id=artifact.correlation_id,
    )


def _load_handoff_payload(*, package_dir: Path) -> ReviewOutcomePackagePayload:
    payload = _read_json_dict(
        path=package_dir / "handoff_payload.json",
        missing_error="cryp_confirmation_export_missing_handoff_payload",
    )
    try:
        return ReviewOutcomePackagePayload.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"cryp_confirmation_export_invalid_handoff_payload:{exc}") from exc


def _load_operator_review(
    *, handoff_payload: ReviewOutcomePackagePayload
) -> OperatorReviewDecisionRecord:
    payload = _read_json_dict(
        path=Path(handoff_payload.operator_review_metadata_path),
        missing_error="cryp_confirmation_export_missing_operator_review_metadata",
    )
    try:
        return OperatorReviewDecisionRecord.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"cryp_confirmation_export_invalid_operator_review:{exc}") from exc


def _validate_reviewed_approved_package(
    *,
    handoff_payload: ReviewOutcomePackagePayload,
    operator_review: OperatorReviewDecisionRecord,
) -> None:
    if handoff_payload.run_status != "success":
        raise ValueError("cryp_confirmation_export_requires_successful_run")
    if handoff_payload.review_status != "decided":
        raise ValueError("cryp_confirmation_export_requires_decided_review")
    if handoff_payload.operator_decision != "approve":
        raise ValueError("cryp_confirmation_export_requires_approved_review")
    if operator_review.artifact.run_id != handoff_payload.run_id:
        raise ValueError("cryp_confirmation_export_run_id_mismatch")
    if operator_review.review_status != handoff_payload.review_status:
        raise ValueError("cryp_confirmation_export_review_status_mismatch")
    if operator_review.operator_decision != handoff_payload.operator_decision:
        raise ValueError("cryp_confirmation_export_operator_decision_mismatch")


def _load_reviewed_signal(
    *, handoff_payload: ReviewOutcomePackagePayload
) -> ReviewedPolymarketExternalConfirmationSignal:
    source_payload = _read_json_dict(
        path=Path(handoff_payload.json_artifact_path),
        missing_error="cryp_confirmation_export_missing_json_artifact",
    )
    signal_payload = source_payload.get(_SOURCE_SIGNAL_KEY)
    if not isinstance(signal_payload, dict):
        raise ValueError(f"cryp_confirmation_export_missing_signal_block:{_SOURCE_SIGNAL_KEY}")
    try:
        return ReviewedPolymarketExternalConfirmationSignal.model_validate(signal_payload)
    except ValidationError as exc:
        raise ValueError(f"cryp_confirmation_export_invalid_signal_block:{exc}") from exc


def _map_signal_to_cryp_bias(
    signal: Literal["buy", "sell", "veto"],
) -> tuple[Literal["buy", "sell", "neutral"], bool]:
    if signal == "buy":
        return "buy", False
    if signal == "sell":
        return "sell", False
    return "neutral", True


def _read_json_dict(*, path: Path, missing_error: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{missing_error}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"cryp_confirmation_export_invalid_json: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"cryp_confirmation_export_invalid_json_object: {path}")
    return payload


__all__ = [
    "CrypExternalConfirmationArtifact",
    "CrypExternalConfirmationExportResult",
    "ReviewedPolymarketExternalConfirmationSignal",
    "build_cryp_external_confirmation_artifact_from_package",
    "write_cryp_external_confirmation_artifact_from_package",
]
