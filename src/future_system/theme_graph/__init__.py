"""Canonical theme graph bridge for deterministic Polymarket linking."""

from future_system.theme_graph.linker import (
    build_theme_link_packet,
    link_market_to_theme_packet,
)
from future_system.theme_graph.loader import (
    ThemeLoadError,
    load_theme_definitions,
    load_theme_registry,
)
from future_system.theme_graph.matcher import match_theme_candidates
from future_system.theme_graph.models import (
    AssetThemeLink,
    ExpectedRelationship,
    NewsEntityLink,
    NormalizedPolymarketMetadata,
    PolymarketThemeLink,
    ThemeDefinition,
    ThemeLinkPacket,
    ThemeMatchCandidate,
    ThemeMatchResult,
)
from future_system.theme_graph.registry import ThemeRegistry
from future_system.theme_graph.validators import ThemeValidationError

__all__ = [
    "AssetThemeLink",
    "ExpectedRelationship",
    "NewsEntityLink",
    "NormalizedPolymarketMetadata",
    "PolymarketThemeLink",
    "ThemeDefinition",
    "ThemeLinkPacket",
    "ThemeLoadError",
    "ThemeMatchCandidate",
    "ThemeMatchResult",
    "ThemeRegistry",
    "ThemeValidationError",
    "build_theme_link_packet",
    "link_market_to_theme_packet",
    "load_theme_definitions",
    "load_theme_registry",
    "match_theme_candidates",
]
