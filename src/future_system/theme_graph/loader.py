"""Synchronous deterministic loader for canonical theme definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from future_system.theme_graph.models import ThemeDefinition
from future_system.theme_graph.registry import ThemeRegistry
from future_system.theme_graph.validators import (
    ThemeValidationError,
    validate_unique_theme_ids,
)

try:  # pragma: no cover - import guard exercised in tests via behavior.
    import yaml  # type: ignore[import-untyped]
except ModuleNotFoundError:  # pragma: no cover - fallback path covered by behavior tests.
    yaml = None


class ThemeLoadError(ValueError):
    """Raised when theme files cannot be loaded into canonical definitions."""


def load_theme_definitions(directory: str | Path) -> list[ThemeDefinition]:
    """Load and validate all theme definitions from a directory."""

    directory_path = Path(directory)
    if not directory_path.exists():
        raise ThemeLoadError(f"Theme directory does not exist: {directory_path}.")
    if not directory_path.is_dir():
        raise ThemeLoadError(f"Theme path is not a directory: {directory_path}.")

    themes: list[ThemeDefinition] = []
    source_by_theme_id: dict[str, Path] = {}

    for theme_path in _iter_theme_files(directory_path):
        raw_document = _load_yaml_document(theme_path)
        if not isinstance(raw_document, dict):
            raise ThemeLoadError(
                f"Theme file {theme_path} must contain a top-level mapping object."
            )

        try:
            theme = ThemeDefinition.model_validate(raw_document)
        except ValidationError as exc:
            raise ThemeLoadError(
                f"Theme file {theme_path} failed schema validation: {exc}."
            ) from exc

        existing_source = source_by_theme_id.get(theme.theme_id)
        if existing_source is not None:
            raise ThemeLoadError(
                f"Duplicate theme_id {theme.theme_id!r} found in "
                f"{existing_source} and {theme_path}."
            )

        source_by_theme_id[theme.theme_id] = theme_path
        themes.append(theme)

    try:
        validate_unique_theme_ids(theme.theme_id for theme in themes)
    except ThemeValidationError as exc:
        raise ThemeLoadError(str(exc)) from exc

    return themes


def load_theme_registry(directory: str | Path) -> ThemeRegistry:
    """Load theme definitions and register them into an in-memory registry."""

    return ThemeRegistry(load_theme_definitions(directory))


def _iter_theme_files(directory: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
        ],
        key=lambda path: path.name,
    )


def _load_yaml_document(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ThemeLoadError(f"Failed to read theme file {path}: {exc}.") from exc

    if yaml is None:
        return _load_json_compatible_yaml(path=path, text=text)

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ThemeLoadError(f"Invalid YAML in {path}: {exc}.") from exc

    if document is None:
        raise ThemeLoadError(f"Theme file {path} is empty.")
    return document


def _load_json_compatible_yaml(path: Path, text: str) -> Any:
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ThemeLoadError(
            f"YAML parser dependency is unavailable for {path}. Install PyYAML or provide "
            "JSON-compatible YAML content."
        ) from exc
    return document
