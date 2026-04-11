"""Canonical models for deterministic theme graph linking."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from future_system.theme_graph.validators import (
    ThemeValidationError,
    validate_aliases,
    validate_date_ordering,
    validate_outcome_map,
    validate_required_collections,
    validate_unit_interval,
)

ThemeStatus = Literal["active", "watch", "inactive", "resolved"]
ThemeCategory = Literal["macro", "politics", "crypto", "regulatory", "geopolitical", "other"]
PolymarketLinkBasis = Literal["manual", "rule", "pattern"]
AssetType = Literal["spot", "perp", "equity", "etf", "index", "fx", "yield", "volatility"]
AssetRole = Literal["primary_proxy", "confirmation_proxy", "hedge_proxy", "context_only"]
DirectionalBias = Literal["up", "down", "mixed", "unknown"]
AssetLinkBasis = Literal["manual", "rule", "historical", "inferred"]
EntityType = Literal["person", "institution", "country", "company", "instrument", "event"]


def _normalize_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ThemeValidationError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ThemeValidationError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ThemeValidationError(f"{field_name} must be a string when provided.")
    normalized = value.strip()
    return normalized or None


class PolymarketThemeLink(BaseModel):
    """Manual or deterministic Polymarket link binding for a theme."""

    condition_id: str | None = None
    market_slug: str | None = None
    event_slug: str | None = None
    outcome_map: dict[str, str]
    confidence: float
    link_basis: PolymarketLinkBasis
    notes: str | None = None

    @field_validator("condition_id", "market_slug", "event_slug", "notes", mode="before")
    @classmethod
    def _normalize_optional_fields(cls, value: Any, info: Any) -> str | None:
        return _normalize_optional_text(value, info.field_name)

    @model_validator(mode="after")
    def _validate_link(self) -> Self:
        if self.condition_id is None and self.market_slug is None and self.event_slug is None:
            raise ThemeValidationError(
                "PolymarketThemeLink must include at least one of condition_id, market_slug, "
                "or event_slug."
            )

        context_key = self.condition_id or self.market_slug or self.event_slug or "unknown"
        context = f"PolymarketThemeLink[{context_key}]"
        self.outcome_map = validate_outcome_map(outcome_map=self.outcome_map, context=context)
        self.confidence = validate_unit_interval(
            value=self.confidence,
            field_name="confidence",
            context=context,
        )
        return self


class AssetThemeLink(BaseModel):
    """Bounded asset-level relationship for one theme."""

    symbol: str
    asset_type: AssetType
    relevance: float
    role: AssetRole
    direction_if_theme_up: DirectionalBias
    link_basis: AssetLinkBasis

    @field_validator("symbol", mode="before")
    @classmethod
    def _normalize_symbol(cls, value: Any) -> str:
        return _normalize_required_text(value, "symbol").upper()

    @field_validator("relevance")
    @classmethod
    def _validate_relevance(cls, value: float) -> float:
        return validate_unit_interval(
            value=value,
            field_name="relevance",
            context="AssetThemeLink",
        )


class NewsEntityLink(BaseModel):
    """News entity expectation linked to a theme."""

    entity_name: str
    entity_type: EntityType
    relevance: float
    required: bool = False

    @field_validator("entity_name", mode="before")
    @classmethod
    def _normalize_entity_name(cls, value: Any) -> str:
        return _normalize_required_text(value, "entity_name")

    @field_validator("relevance")
    @classmethod
    def _validate_relevance(cls, value: float) -> float:
        return validate_unit_interval(
            value=value,
            field_name="relevance",
            context="NewsEntityLink",
        )


class ExpectedRelationship(BaseModel):
    """Template describing supporting or contradicting relationship behavior."""

    trigger: str
    supporting_moves: list[str]
    contradicting_moves: list[str]
    notes: str | None = None

    @field_validator("trigger", mode="before")
    @classmethod
    def _normalize_trigger(cls, value: Any) -> str:
        return _normalize_required_text(value, "trigger")

    @field_validator("supporting_moves", "contradicting_moves", mode="before")
    @classmethod
    def _normalize_move_lists(cls, value: Any, info: Any) -> list[str]:
        if not isinstance(value, list):
            raise ThemeValidationError(f"{info.field_name} must be a list of strings.")
        normalized = [_normalize_required_text(item, info.field_name) for item in value]
        return normalized

    @field_validator("notes", mode="before")
    @classmethod
    def _normalize_notes(cls, value: Any) -> str | None:
        return _normalize_optional_text(value, "notes")

    @model_validator(mode="after")
    def _validate_relationship(self) -> Self:
        if not self.supporting_moves and not self.contradicting_moves:
            raise ThemeValidationError(
                "ExpectedRelationship must include at least one supporting or contradicting move."
            )
        return self


class ThemeDefinition(BaseModel):
    """Canonical manually curated definition of one theme."""

    theme_id: str
    title: str
    description: str
    status: ThemeStatus
    category: ThemeCategory
    start_at: datetime | None = None
    expected_resolution_at: datetime | None = None
    primary_question: str
    aliases: list[str]
    polymarket_links: list[PolymarketThemeLink]
    asset_links: list[AssetThemeLink]
    news_entities: list[NewsEntityLink]
    relationship_templates: list[ExpectedRelationship]
    review_required: bool = True

    @field_validator("theme_id", "title", "description", "primary_question", mode="before")
    @classmethod
    def _normalize_required_strings(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("aliases", mode="before")
    @classmethod
    def _ensure_aliases_list(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            raise ThemeValidationError("aliases must be a list of strings.")
        return [_normalize_required_text(alias, "aliases") for alias in value]

    @model_validator(mode="after")
    def _validate_theme(self) -> Self:
        self.aliases = validate_aliases(theme_id=self.theme_id, aliases=self.aliases)
        validate_date_ordering(
            theme_id=self.theme_id,
            start_at=self.start_at,
            expected_resolution_at=self.expected_resolution_at,
        )
        validate_required_collections(
            theme_id=self.theme_id,
            collections={
                "aliases": self.aliases,
                "polymarket_links": self.polymarket_links,
                "asset_links": self.asset_links,
                "news_entities": self.news_entities,
                "relationship_templates": self.relationship_templates,
            },
        )
        return self


class ThemeLinkPacket(BaseModel):
    """Deterministic bridge packet from a Polymarket match to a canonical theme."""

    theme_id: str
    matched_polymarket_markets: list[PolymarketThemeLink]
    matched_assets: list[AssetThemeLink]
    matched_entities: list[NewsEntityLink]
    ambiguity_flags: list[str]
    confidence_score: float
    explanation: str

    @field_validator("theme_id", "explanation", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("confidence_score")
    @classmethod
    def _validate_confidence(cls, value: float) -> float:
        return validate_unit_interval(
            value=value,
            field_name="confidence_score",
            context="ThemeLinkPacket",
        )


class NormalizedPolymarketMetadata(BaseModel):
    """Bounded normalized market metadata input for deterministic matching."""

    market_slug: str | None = None
    event_slug: str | None = None
    question: str | None = None
    description: str | None = None
    condition_id: str | None = None

    @field_validator(
        "market_slug",
        "event_slug",
        "question",
        "description",
        "condition_id",
        mode="before",
    )
    @classmethod
    def _normalize_optional_fields(cls, value: Any, info: Any) -> str | None:
        return _normalize_optional_text(value, info.field_name)


class ThemeMatchCandidate(BaseModel):
    """Deterministic scored candidate for a matched theme."""

    theme: ThemeDefinition
    score: float
    reasons: list[str] = Field(default_factory=list)
    matched_polymarket_markets: list[PolymarketThemeLink] = Field(default_factory=list)

    @field_validator("score")
    @classmethod
    def _validate_score(cls, value: float) -> float:
        return validate_unit_interval(
            value=value,
            field_name="score",
            context="ThemeMatchCandidate",
        )


class ThemeMatchResult(BaseModel):
    """Matcher output containing ranked candidates and ambiguity information."""

    market: NormalizedPolymarketMetadata
    candidates: list[ThemeMatchCandidate] = Field(default_factory=list)
    confident_candidate: ThemeMatchCandidate | None = None
    ambiguity_flags: list[str] = Field(default_factory=list)
