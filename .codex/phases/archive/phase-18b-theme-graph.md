You are implementing a bounded architecture phase in an existing repo.

ROLE
You are the implementation engine, not the architect.
Do not redesign the system.
Do not widen scope.
Do not touch unrelated modules.
Preserve current boundaries.

ARCHITECTURAL TRUTH
- `src/polymarket_arb/*` is the bounded Polymarket intelligence/opportunity module.
- `src/future_system/*` is the expansion track for the larger cross-market platform.
- This phase builds the first bridge module inside `future_system`.
- Do NOT mix crypto, stocks, news, AI reasoning, UI, or live execution into this phase.
- Do NOT refactor `polymarket_arb` unless strictly required for imports/types and even then prefer not to.

PHASE NAME
Phase 1: Canonical Theme Graph

PHASE OBJECTIVE
Build `src/future_system/theme_graph/` as the canonical theme-linking layer that:
1. loads manually curated theme definitions from YAML
2. validates them deterministically
3. registers them in memory
4. matches normalized Polymarket market metadata to candidate themes
5. emits deterministic theme link packets
6. flags ambiguity when multiple themes compete

WHY THIS PHASE EXISTS
The larger system needs a hard bridge between Polymarket event markets and future external evidence sources.
This module provides structure only.
It does not fetch live data.
It does not make decisions.
It does not use LLMs.

IN SCOPE
Create these files if they do not already exist:

- `src/future_system/theme_graph/__init__.py`
- `src/future_system/theme_graph/models.py`
- `src/future_system/theme_graph/loader.py`
- `src/future_system/theme_graph/registry.py`
- `src/future_system/theme_graph/matcher.py`
- `src/future_system/theme_graph/linker.py`
- `src/future_system/theme_graph/validators.py`

Create tests:

- `tests/future_system/test_theme_graph_models.py`
- `tests/future_system/test_theme_graph_loader.py`
- `tests/future_system/test_theme_graph_matcher.py`

Create YAML fixtures:

- `tests/fixtures/future_system/themes/fed_rate_cut_june_2026.yaml`
- `tests/fixtures/future_system/themes/btc_spot_etf_approval.yaml`
- `tests/fixtures/future_system/themes/us_election_2028.yaml`

If there is an existing fixtures convention in the repo, follow it.

OUT OF SCOPE
Do NOT build or touch:
- crypto adapters
- macro adapters
- news adapters
- divergence engine
- evidence assembly
- LLM prompts/reasoning
- policy engine
- execution logic
- dashboard/UI
- database persistence
- network calls
- background jobs
- repo-wide refactors

DO NOT TOUCH
- `src/polymarket_arb/*`
- live trade code
- API routes unrelated to this module
- existing CLI behavior
unless absolutely required for test imports, and even then keep changes minimal and explain them.

DESIGN REQUIREMENTS

1. MODELS
Implement strongly typed models, using the repo’s existing model style if one exists. Prefer Pydantic if already used; otherwise follow local conventions.

Required core objects:

- `ThemeDefinition`
- `PolymarketThemeLink`
- `AssetThemeLink`
- `NewsEntityLink`
- `ExpectedRelationship`
- `ThemeLinkPacket`

Suggested fields:

ThemeDefinition
- `theme_id: str`
- `title: str`
- `description: str`
- `status: Literal["active", "watch", "inactive", "resolved"]`
- `category: Literal["macro", "politics", "crypto", "regulatory", "geopolitical", "other"]`
- `start_at: datetime | None`
- `expected_resolution_at: datetime | None`
- `primary_question: str`
- `aliases: list[str]`
- `polymarket_links: list[PolymarketThemeLink]`
- `asset_links: list[AssetThemeLink]`
- `news_entities: list[NewsEntityLink]`
- `relationship_templates: list[ExpectedRelationship]`
- `review_required: bool = True`

PolymarketThemeLink
- `condition_id: str | None`
- `market_slug: str | None`
- `event_slug: str | None`
- `outcome_map: dict[str, str]`
- `confidence: float`
- `link_basis: Literal["manual", "rule", "pattern"]`
- `notes: str | None`

AssetThemeLink
- `symbol: str`
- `asset_type: Literal["spot", "perp", "equity", "etf", "index", "fx", "yield", "volatility"]`
- `relevance: float`
- `role: Literal["primary_proxy", "confirmation_proxy", "hedge_proxy", "context_only"]`
- `direction_if_theme_up: Literal["up", "down", "mixed", "unknown"]`
- `link_basis: Literal["manual", "rule", "historical", "inferred"]`

NewsEntityLink
- `entity_name: str`
- `entity_type: Literal["person", "institution", "country", "company", "instrument", "event"]`
- `relevance: float`
- `required: bool = False`

ExpectedRelationship
- `trigger: str`
- `supporting_moves: list[str]`
- `contradicting_moves: list[str]`
- `notes: str | None`

ThemeLinkPacket
- `theme_id: str`
- `matched_polymarket_markets: list[PolymarketThemeLink]`
- `matched_assets: list[AssetThemeLink]`
- `matched_entities: list[NewsEntityLink]`
- `ambiguity_flags: list[str]`
- `confidence_score: float`
- `explanation: str`

2. LOADER
Implement YAML loading from a directory of theme definitions.
Requirements:
- deterministic load order
- reject duplicate `theme_id`
- validate required fields
- reject malformed theme definitions with useful errors
- keep behavior synchronous and simple

3. REGISTRY
Implement in-memory registry for loaded themes.
Requirements:
- get by `theme_id`
- list all
- detect duplicates
- optionally basic lookup by alias if clean to add

4. MATCHER
Implement deterministic candidate matching from a normalized Polymarket market metadata object to one or more themes.

Assume the matcher receives a simple normalized input object or dict with fields like:
- `market_slug`
- `event_slug`
- `question`
- `description`
- `condition_id`

Do NOT fetch data.
Do NOT call Polymarket.
Do NOT infer from outside sources.

Matching should rely on:
- exact `condition_id` if present
- exact `market_slug`
- exact `event_slug`
- alias/title/question text overlap as fallback
- deterministic scoring
- ambiguity flags when more than one strong match exists

5. LINKER
Implement creation of `ThemeLinkPacket` from:
- a matched theme
- the corresponding matched Polymarket links
- ambiguity info
- deterministic confidence score
- short explanation string

6. VALIDATORS
Add focused validation helpers for:
- duplicate theme ids
- duplicate aliases within a theme if problematic
- invalid date ordering
- empty required collections where inappropriate
- malformed outcome maps
- invalid confidence/relevance ranges

BEHAVIORAL RULES
- deterministic only
- no LLM use
- no random scoring
- no hidden network assumptions
- no speculative linking to external assets beyond what YAML defines
- prefer exact/manual mapping over fuzzy matching
- when fuzzy matching is weak, return no confident match instead of inventing one

FIXTURE REQUIREMENTS
Create 3 valid YAML theme fixtures:

1. `fed_rate_cut_june_2026.yaml`
2. `btc_spot_etf_approval.yaml`
3. `us_election_2028.yaml`

Each fixture should:
- be realistic
- include aliases
- include at least one `polymarket_links` entry
- include at least one `asset_links` entry
- include at least one `news_entities` entry
- include at least one `relationship_templates` entry

TEST REQUIREMENTS

`test_theme_graph_models.py`
- model accepts valid objects
- model rejects invalid enums/ranges where applicable
- invalid date ordering is caught if validator enforces it

`test_theme_graph_loader.py`
- loads all fixture themes
- returns deterministic order if applicable
- rejects duplicate `theme_id`
- rejects malformed YAML / malformed schema

`test_theme_graph_matcher.py`
- exact `market_slug` match works
- exact `event_slug` match works if configured
- exact `condition_id` match wins if present
- ambiguous case returns ambiguity flags
- weak/unmatched case returns no confident result
- linker emits deterministic `ThemeLinkPacket`

IMPLEMENTATION CONSTRAINTS
- Keep code small and explicit
- Prefer pure functions where possible
- Keep imports local and clean
- Avoid framework sprawl
- Follow existing repo code style and test style
- Do not add dependencies unless absolutely necessary
- If YAML parsing dependency already exists, use it
- If not, use the smallest acceptable dependency already present in repo or note requirement clearly

ACCEPTANCE CRITERIA
This phase is complete only if all are true:

1. `theme_graph` module exists with the files listed above
2. valid YAML fixtures load successfully
3. duplicate theme ids are rejected
4. deterministic matching works for known Polymarket inputs
5. ambiguity is surfaced explicitly
6. linker emits structured `ThemeLinkPacket`
7. tests pass
8. no unrelated modules were modified
9. no crypto/news/macro/LLM logic was introduced

VALIDATION
Before finishing:
- inspect repo for test/lint/typecheck commands and use the narrowest ones that validate this phase
- run only relevant tests first
- run any project formatter/linter only if required by repo norms and keep scope narrow

At minimum, run:
- targeted tests for the new module
- any local type/lint checks necessary for touched files

FINAL OUTPUT FORMAT
Return:
1. concise summary of what was built
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. any deviations from spec
6. note explicitly whether `src/polymarket_arb/*` was untouched

IMPORTANT
Do not widen the phase.
Do not “helpfully” add future phases.
Do not start implementing evidence, divergence, or adapters.
Complete only this bounded phase.
