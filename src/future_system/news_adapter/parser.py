"""Deterministic fixture-oriented parser for normalized news records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, cast

from pydantic import ValidationError

from future_system.news_adapter.filters import apply_news_record_filter
from future_system.news_adapter.models import (
    NewsAdapterError,
    NewsAdapterParseResult,
    NewsRecordFilter,
    NewsSource,
    NewsSourceType,
    NormalizedNewsRecord,
)


def parse_news_records(
    payload: Sequence[Mapping[str, Any]] | Mapping[str, Any],
) -> NewsAdapterParseResult:
    """Parse raw fixture payload into deterministic normalized news records."""

    records = _extract_records(payload)

    normalized_records: list[NormalizedNewsRecord] = []
    skipped_records = 0
    flags: set[str] = set()

    for record in records:
        try:
            normalized_records.append(_normalize_record(record=record))
        except (TypeError, ValueError, ValidationError):
            skipped_records += 1

    if skipped_records > 0:
        flags.add("skipped_invalid_records")

    publisher_count = len({record.publisher for record in normalized_records})
    return NewsAdapterParseResult(
        publisher_count=publisher_count,
        records=normalized_records,
        skipped_records=skipped_records,
        flags=sorted(flags),
    )


class FixtureNewsAdapter:
    """Tiny protocol-compatible adapter for deterministic fixture parsing."""

    def parse_raw_payload(
        self,
        payload: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    ) -> NewsAdapterParseResult:
        return parse_news_records(payload)

    def filter_records(
        self,
        records: Sequence[NormalizedNewsRecord],
        *,
        record_filter: NewsRecordFilter | None = None,
    ) -> list[NormalizedNewsRecord]:
        return apply_news_record_filter(records=records, record_filter=record_filter)


def _extract_records(
    payload: Sequence[Mapping[str, Any]] | Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    if isinstance(payload, Mapping):
        if "records" in payload:
            records_raw = payload["records"]
            if not isinstance(records_raw, Sequence) or isinstance(records_raw, str | bytes):
                raise NewsAdapterError("payload['records'] must be a sequence of mappings.")

            records: list[Mapping[str, Any]] = []
            for item in records_raw:
                if not isinstance(item, Mapping):
                    raise NewsAdapterError("payload records must be mappings.")
                records.append(item)
            return records
        return [payload]

    if not isinstance(payload, Sequence) or isinstance(payload, str | bytes):
        raise NewsAdapterError("payload must be a sequence of mappings or a mapping.")

    records = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise NewsAdapterError("payload sequence items must be mappings.")
        records.append(item)
    return records


def _normalize_record(*, record: Mapping[str, Any]) -> NormalizedNewsRecord:
    source = _normalize_source(record.get("source", "fixture"))
    source_type = _normalize_source_type(record.get("source_type", "other"))
    is_official_source = _coerce_optional_bool(record.get("is_official_source"))

    if is_official_source is None:
        is_official_source = source_type == "official"

    return NormalizedNewsRecord(
        source=source,
        publisher=_coerce_required_text(record.get("publisher"), "publisher"),
        source_type=source_type,
        article_id=_coerce_required_text(record.get("article_id", record.get("id")), "article_id"),
        headline=_coerce_required_text(record.get("headline", record.get("title")), "headline"),
        summary=_coerce_optional_text(record.get("summary", record.get("description"))),
        url=_coerce_optional_text(record.get("url", record.get("link"))),
        published_at=_coerce_datetime(record.get("published_at", record.get("published"))),
        ingested_at=_coerce_optional_datetime(record.get("ingested_at", record.get("ingested"))),
        entities=_coerce_string_list(record.get("entities")),
        topics=_coerce_string_list(record.get("topics")),
        trust_score=_coerce_required_float(record.get("trust_score"), "trust_score"),
        language=_coerce_optional_text(record.get("language")),
        is_official_source=is_official_source,
    )


def _normalize_source(value: Any) -> NewsSource:
    raw = _coerce_required_text(value, "source").casefold()
    if raw not in {"fixture", "api", "feed"}:
        raise ValueError("source must be one of fixture, api, feed.")
    return cast(NewsSource, raw)


def _normalize_source_type(value: Any) -> NewsSourceType:
    raw = _coerce_required_text(value, "source_type").casefold()
    if raw not in {"wire", "official", "newsroom", "analysis", "other"}:
        raise ValueError("source_type must be one of wire, official, newsroom, analysis, other.")
    return cast(NewsSourceType, raw)


def _coerce_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return normalized


def _coerce_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return _coerce_required_text(value, "value")


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("entities/topics fields must be lists of strings.")

    output: list[str] = []
    for item in value:
        output.append(_coerce_required_text(item, "list_item"))
    return output


def _coerce_required_float(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric.")
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return float(value.strip())
    raise ValueError(f"{field_name} must be numeric.")


def _coerce_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value in {0, 1}:
            return bool(value)
        raise ValueError("boolean integer values must be 0 or 1.")
    if isinstance(value, str):
        raw = value.strip().casefold()
        if raw in {"true", "1", "yes"}:
            return True
        if raw in {"false", "0", "no"}:
            return False
    raise ValueError("invalid boolean value.")


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise ValueError("published_at/published must be an ISO datetime string.")


def _coerce_optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return _coerce_datetime(value)
