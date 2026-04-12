"""Canonical models for deterministic opportunity context bundle assembly."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.theme_graph.models import ThemeLinkPacket

BundleComponentStatus = Literal["present", "partial", "missing"]


def _normalize_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided.")
    normalized = value.strip()
    return normalized or None


def _validate_unit_interval(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be within [0.0, 1.0]; received {value}.")
    return value


class BundleQualitySummary(BaseModel):
    """Deterministic bundle-level quality and completeness summary."""

    completeness_score: float
    freshness_score: float
    confidence_score: float
    conflict_score: float
    component_statuses: dict[str, BundleComponentStatus]
    flags: list[str] = Field(default_factory=list)

    @field_validator(
        "completeness_score",
        "freshness_score",
        "confidence_score",
        "conflict_score",
    )
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated

    @field_validator("component_statuses", mode="before")
    @classmethod
    def _validate_component_statuses(cls, value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            raise ValueError("component_statuses must be a dict[str, BundleComponentStatus].")
        normalized: dict[str, str] = {}
        for key, status in value.items():
            normalized_key = _normalize_required_text(key, "component_statuses.key")
            normalized[normalized_key] = _normalize_required_text(
                status,
                "component_statuses.value",
            )
        return normalized

    @field_validator("flags", mode="before")
    @classmethod
    def _normalize_flags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("flags must be a list of strings.")

        normalized: list[str] = []
        for raw in value:
            flag = _normalize_required_text(raw, "flags")
            if flag in normalized:
                continue
            normalized.append(flag)
        return normalized


class OpportunityContextBundle(BaseModel):
    """Canonical context bundle joining all upstream theme-scoped packets."""

    theme_id: str
    title: str | None = None
    theme_link: ThemeLinkPacket
    polymarket_evidence: ThemeEvidencePacket
    divergence: ThemeDivergencePacket
    crypto_evidence: ThemeCryptoEvidencePacket
    comparison: ThemeComparisonPacket
    news_evidence: ThemeNewsEvidencePacket
    candidate: CandidateSignalPacket
    quality: BundleQualitySummary
    operator_summary: str
    flags: list[str] = Field(default_factory=list)

    @field_validator("theme_id", "operator_summary", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("title", mode="before")
    @classmethod
    def _normalize_optional_title(cls, value: Any) -> str | None:
        return _normalize_optional_text(value, "title")

    @field_validator("flags", mode="before")
    @classmethod
    def _normalize_flags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("flags must be a list of strings.")

        normalized: list[str] = []
        for raw in value:
            flag = _normalize_required_text(raw, "flags")
            if flag in normalized:
                continue
            normalized.append(flag)
        return normalized


class ContextBundleError(ValueError):
    """Raised when canonical opportunity context bundling cannot be completed."""
