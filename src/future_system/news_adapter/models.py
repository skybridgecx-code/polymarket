"""Canonical models for deterministic news adapter normalization."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

NewsSource = Literal["fixture", "api", "feed"]
NewsSourceType = Literal["wire", "official", "newsroom", "analysis", "other"]


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
    return _normalize_required_text(value, field_name)


def _normalize_match_token(value: str) -> str:
    return " ".join(value.split()).casefold()


def normalize_news_list(values: list[str]) -> list[str]:
    """Normalize list tokens with case-insensitive dedupe and stable ordering."""

    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values:
        token = _normalize_match_token(_normalize_required_text(raw, "list_item"))
        if not token:
            continue
        if token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    return normalized


class NormalizedNewsRecord(BaseModel):
    """Canonical normalized news/article/headline record."""

    source: NewsSource
    publisher: str
    source_type: NewsSourceType
    article_id: str
    headline: str
    summary: str | None = None
    url: str | None = None
    published_at: datetime
    ingested_at: datetime | None = None
    entities: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    trust_score: float
    language: str | None = None
    is_official_source: bool = False

    @field_validator("publisher", mode="before")
    @classmethod
    def _normalize_publisher(cls, value: Any) -> str:
        return _normalize_match_token(_normalize_required_text(value, "publisher"))

    @field_validator("article_id", "headline", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("summary", "url", "language", mode="before")
    @classmethod
    def _normalize_optional_fields(cls, value: Any, info: Any) -> str | None:
        normalized = _normalize_optional_text(value, info.field_name)
        if normalized is None:
            return None
        if info.field_name == "language":
            return normalized.casefold()
        return normalized

    @field_validator("entities", "topics", mode="before")
    @classmethod
    def _normalize_string_lists(cls, value: Any, info: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError(f"{info.field_name} must be a list of strings.")
        normalized_inputs = [_normalize_required_text(item, info.field_name) for item in value]
        return normalize_news_list(normalized_inputs)

    @field_validator("trust_score")
    @classmethod
    def _validate_trust_score(cls, value: float) -> float:
        if value < 0.0 or value > 1.0:
            raise ValueError(f"trust_score must be within [0.0, 1.0]; received {value}.")
        return value


class NewsAdapterParseResult(BaseModel):
    """Deterministic parser output containing normalized news records."""

    publisher_count: int
    records: list[NormalizedNewsRecord] = Field(default_factory=list)
    skipped_records: int = 0
    flags: list[str] = Field(default_factory=list)

    @field_validator("publisher_count", "skipped_records")
    @classmethod
    def _validate_non_negative_counts(cls, value: int, info: Any) -> int:
        if value < 0:
            raise ValueError(f"{info.field_name} cannot be negative.")
        return value

    @field_validator("flags", mode="before")
    @classmethod
    def _normalize_flags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("flags must be a list of strings.")

        normalized: list[str] = []
        for raw in value:
            normalized_flag = _normalize_required_text(raw, "flags")
            if normalized_flag in normalized:
                continue
            normalized.append(normalized_flag)
        return normalized


class NewsRecordFilter(BaseModel):
    """Deterministic exact-match filter input for normalized news records."""

    publisher: str | None = None
    entity: str | None = None
    topic: str | None = None
    official_only: bool | None = None
    published_at_gte: datetime | None = None

    @field_validator("publisher", "entity", "topic", mode="before")
    @classmethod
    def _normalize_optional_tokens(cls, value: Any, info: Any) -> str | None:
        normalized = _normalize_optional_text(value, info.field_name)
        if normalized is None:
            return None
        return _normalize_match_token(normalized)


class NewsAdapterError(ValueError):
    """Raised when raw payloads cannot be parsed into normalized news records."""
