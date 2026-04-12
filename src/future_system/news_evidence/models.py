"""Canonical contracts for deterministic theme-linked news evidence assembly."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

NewsSourceType = Literal["wire", "official", "newsroom", "analysis", "other"]


def _normalize_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_match_token(value: str) -> str:
    return " ".join(value.split()).casefold()


def _normalize_string_list(values: Any, field_name: str) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list of strings.")

    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values:
        token = _normalize_match_token(_normalize_required_text(raw, field_name))
        if token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    return normalized


def _validate_unit_interval(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be within [0.0, 1.0]; received {value}.")
    return value


class MatchedNewsEvidence(BaseModel):
    """Theme-scoped evidence summary for one matched normalized news record."""

    article_id: str
    publisher: str
    source_type: NewsSourceType
    headline: str
    published_at: datetime
    trust_score: float
    freshness_score: float
    match_reasons: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    is_primary: bool = False

    @field_validator("article_id", "headline", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("publisher", mode="before")
    @classmethod
    def _normalize_publisher(cls, value: Any) -> str:
        return _normalize_match_token(_normalize_required_text(value, "publisher"))

    @field_validator("trust_score", "freshness_score")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated

    @field_validator("match_reasons", "flags", mode="before")
    @classmethod
    def _normalize_reason_and_flag_lists(cls, value: Any, info: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError(f"{info.field_name} must be a list of strings.")

        normalized: list[str] = []
        for raw in value:
            token = _normalize_required_text(raw, info.field_name)
            if token in normalized:
                continue
            normalized.append(token)
        return normalized

    @field_validator("entities", "topics", mode="before")
    @classmethod
    def _normalize_entities_topics(cls, value: Any, info: Any) -> list[str]:
        return _normalize_string_list(value, info.field_name)


class ThemeNewsEvidencePacket(BaseModel):
    """Canonical news evidence output packet for one linked theme."""

    theme_id: str
    primary_article_id: str | None
    matched_records: list[MatchedNewsEvidence]
    matched_article_count: int
    freshness_score: float
    trust_score: float
    coverage_score: float
    official_source_present: bool
    flags: list[str] = Field(default_factory=list)
    explanation: str

    @field_validator("theme_id", "explanation", mode="before")
    @classmethod
    def _normalize_required_packet_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("primary_article_id", mode="before")
    @classmethod
    def _normalize_optional_article_id(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _normalize_required_text(value, "primary_article_id")

    @field_validator("matched_article_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("matched_article_count cannot be negative.")
        return value

    @field_validator("freshness_score", "trust_score", "coverage_score")
    @classmethod
    def _validate_packet_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated

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

    @model_validator(mode="after")
    def _validate_record_count(self) -> Self:
        if self.matched_article_count != len(self.matched_records):
            raise ValueError("matched_article_count must equal len(matched_records).")
        return self


class NewsEvidenceAssemblyError(ValueError):
    """Raised when theme-linked news evidence cannot be assembled deterministically."""
