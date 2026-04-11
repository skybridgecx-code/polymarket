"""Focused validation helpers for canonical theme graph definitions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime


class ThemeValidationError(ValueError):
    """Raised when a theme definition violates canonical constraints."""


def validate_unique_theme_ids(theme_ids: Iterable[str]) -> None:
    """Reject duplicate theme identifiers."""

    seen: set[str] = set()
    duplicates: set[str] = set()

    for raw_theme_id in theme_ids:
        theme_id = raw_theme_id.strip()
        if not theme_id:
            raise ThemeValidationError("theme_id must be a non-empty string.")
        if theme_id in seen:
            duplicates.add(theme_id)
        seen.add(theme_id)

    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ThemeValidationError(f"Duplicate theme_id values detected: {duplicate_text}.")


def validate_aliases(theme_id: str, aliases: Iterable[str]) -> list[str]:
    """Normalize aliases and reject duplicates after case-folding."""

    cleaned_aliases: list[str] = []
    seen: set[str] = set()
    duplicates: set[str] = set()

    for raw_alias in aliases:
        alias = raw_alias.strip()
        if not alias:
            raise ThemeValidationError(f"Theme {theme_id!r} contains an empty alias.")
        alias_key = alias.casefold()
        if alias_key in seen:
            duplicates.add(alias)
            continue
        seen.add(alias_key)
        cleaned_aliases.append(alias)

    if not cleaned_aliases:
        raise ThemeValidationError(f"Theme {theme_id!r} must define at least one alias.")
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ThemeValidationError(
            f"Theme {theme_id!r} has duplicate aliases after normalization: {duplicate_text}."
        )
    return cleaned_aliases


def validate_date_ordering(
    *,
    theme_id: str,
    start_at: datetime | None,
    expected_resolution_at: datetime | None,
) -> None:
    """Ensure expected resolution is not before theme start."""

    if start_at is None or expected_resolution_at is None:
        return
    if expected_resolution_at < start_at:
        raise ThemeValidationError(
            f"Theme {theme_id!r} has invalid date ordering: "
            "expected_resolution_at must be on or after start_at."
        )


def validate_required_collections(
    *,
    theme_id: str,
    collections: Mapping[str, Iterable[object]],
) -> None:
    """Reject empty collections for required relationship fields."""

    for collection_name, values in collections.items():
        if not list(values):
            raise ThemeValidationError(
                f"Theme {theme_id!r} must include at least one {collection_name} entry."
            )


def validate_outcome_map(
    *,
    outcome_map: Mapping[str, str],
    context: str,
) -> dict[str, str]:
    """Validate and normalize a Polymarket outcome map."""

    if not outcome_map:
        raise ThemeValidationError(f"{context}: outcome_map must not be empty.")

    cleaned: dict[str, str] = {}
    seen_keys: set[str] = set()
    for raw_key, raw_value in outcome_map.items():
        key = raw_key.strip()
        value = raw_value.strip()
        if not key or not value:
            raise ThemeValidationError(
                f"{context}: outcome_map keys and values must be non-empty strings."
            )
        normalized_key = key.casefold()
        if normalized_key in seen_keys:
            raise ThemeValidationError(
                f"{context}: outcome_map contains duplicate key {key!r} after normalization."
            )
        seen_keys.add(normalized_key)
        cleaned[key] = value

    return cleaned


def validate_unit_interval(*, value: float, field_name: str, context: str) -> float:
    """Validate that a confidence/relevance score sits within [0.0, 1.0]."""

    if value < 0.0 or value > 1.0:
        raise ThemeValidationError(
            f"{context}: {field_name} must be within [0.0, 1.0]; received {value}."
        )
    return value
