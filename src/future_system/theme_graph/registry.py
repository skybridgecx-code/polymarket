"""In-memory registry for canonical theme definitions."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from future_system.theme_graph.models import ThemeDefinition
from future_system.theme_graph.validators import ThemeValidationError


class ThemeRegistry:
    """Deterministic in-memory registry for loaded themes."""

    def __init__(self, themes: Iterable[ThemeDefinition] | None = None) -> None:
        self._themes_by_id: dict[str, ThemeDefinition] = {}
        self._ordered_theme_ids: list[str] = []
        self._themes_by_alias: dict[str, list[ThemeDefinition]] = defaultdict(list)

        if themes is not None:
            for theme in themes:
                self.register(theme)

    def register(self, theme: ThemeDefinition) -> None:
        """Register one theme, rejecting duplicate theme identifiers."""

        if theme.theme_id in self._themes_by_id:
            raise ThemeValidationError(
                f"Duplicate theme_id during registration: {theme.theme_id!r}."
            )

        self._themes_by_id[theme.theme_id] = theme
        self._ordered_theme_ids.append(theme.theme_id)
        for alias in theme.aliases:
            self._themes_by_alias[_normalize_lookup_key(alias)].append(theme)

    def get(self, theme_id: str) -> ThemeDefinition | None:
        """Fetch a single theme by theme_id."""

        return self._themes_by_id.get(theme_id)

    def list_all(self) -> list[ThemeDefinition]:
        """List all themes in deterministic registration order."""

        return [self._themes_by_id[theme_id] for theme_id in self._ordered_theme_ids]

    def find_by_alias(self, alias: str) -> list[ThemeDefinition]:
        """Return all themes mapped to a normalized alias."""

        return list(self._themes_by_alias.get(_normalize_lookup_key(alias), []))

    def get_unique_by_alias(self, alias: str) -> ThemeDefinition | None:
        """Return a unique alias match when exactly one theme maps to it."""

        themes = self.find_by_alias(alias)
        if len(themes) == 1:
            return themes[0]
        return None

    def __len__(self) -> int:
        return len(self._themes_by_id)


def _normalize_lookup_key(value: str) -> str:
    return value.strip().casefold()
