# Phase 18J — Theme-Linked News Evidence Assembly

## Role
You are the implementation engine, not the architect.

Do not redesign the system.
Do not widen scope.
Do not touch unrelated modules.
Preserve current boundaries.

## Architectural truth
- `src/polymarket_arb/*` remains the bounded Polymarket intelligence/opportunity module.
- `src/future_system/theme_graph/*` is the canonical theme-linking layer.
- `src/future_system/evidence/*` is the canonical Polymarket evidence layer.
- `src/future_system/divergence/*` is the deterministic disagreement layer.
- `src/future_system/crypto_adapter/*` is the normalized crypto source boundary.
- `src/future_system/crypto_evidence/*` is the theme-linked crypto evidence layer.
- `src/future_system/comparison/*` is the deterministic Polymarket-vs-crypto comparison layer.
- `src/future_system/candidates/*` is the candidate signal layer.
- `src/future_system/news_adapter/*` is the normalized news source boundary.
- This phase adds the missing bridge from theme-linked definitions + normalized news records into a canonical theme-scoped news evidence packet.
- This phase is deterministic assembly only.
- Do not add live fetches, scraping, schedulers, reasoning, policy, execution, UI, storage, or mixed-family merger logic.

## Why this phase exists
The system now knows:
- what themes are
- what entities/topics matter to a theme
- how to parse normalized news records

But it still cannot answer:
- what is the current news evidence for this theme
- which records matched the theme
- how fresh and trustworthy that matched news set is
- whether the theme has decent news coverage or almost none

This phase creates that canonical news evidence layer.

## Phase objective
Build `src/future_system/news_evidence/` so the system can:

1. accept a `ThemeLinkPacket`
2. accept one or more `NormalizedNewsRecord` inputs
3. select only the news records relevant to the linked theme entities/topics
4. compute deterministic freshness / trust / coverage summaries
5. emit a canonical `ThemeNewsEvidencePacket`

This phase does not do reasoning.
This phase does not compare news to Polymarket or crypto yet.
This phase does not perform contradiction analysis yet.

## In scope

Create these files if they do not already exist:

- `src/future_system/news_evidence/__init__.py`
- `src/future_system/news_evidence/models.py`
- `src/future_system/news_evidence/assembler.py`
- `src/future_system/news_evidence/scoring.py`

Create tests:

- `tests/future_system/test_news_evidence_models.py`
- `tests/future_system/test_news_evidence_assembler.py`
- `tests/future_system/test_news_evidence_scoring.py`

Create fixtures:

- `tests/fixtures/future_system/news/theme_news_records.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- live HTTP/news clients
- scraping
- scheduler / polling jobs
- contradiction engine
- mixed-family evidence merger
- Polymarket-vs-news comparison
- crypto-vs-news comparison
- reasoning / prompts / LLM logic
- policy engine
- execution logic
- CLI/API surfaces
- dashboard/UI
- persistence/database
- repo-wide refactors

## Do not touch
- `src/polymarket_arb/*`
- trade service / live order code
- existing CLI behavior
- unrelated phase docs

If imports require tiny changes elsewhere, keep them minimal and explain them.

## Required models

Implement strongly typed models using existing repo conventions.

### 1. `MatchedNewsEvidence`
Represents one matched news record’s theme-scoped evidence.

Suggested fields:
- `article_id: str`
- `publisher: str`
- `source_type: Literal["wire", "official", "newsroom", "analysis", "other"]`
- `headline: str`
- `published_at: datetime`
- `trust_score: float`
- `freshness_score: float`
- `match_reasons: list[str]`
- `entities: list[str]`
- `topics: list[str]`
- `flags: list[str]`
- `is_primary: bool = False`

### 2. `ThemeNewsEvidencePacket`
Canonical news evidence output for one theme.

Suggested fields:
- `theme_id: str`
- `primary_article_id: str | None`
- `matched_records: list[MatchedNewsEvidence]`
- `matched_article_count: int`
- `freshness_score: float`
- `trust_score: float`
- `coverage_score: float`
- `official_source_present: bool`
- `flags: list[str]`
- `explanation: str`

### 3. `NewsEvidenceAssemblyError`
Raised when assembly cannot build a valid packet from the provided theme links and normalized news records.

## Assembly behavior

Implement deterministic assembly from:
- `ThemeLinkPacket`
- sequence of `NormalizedNewsRecord` or plain mappings that validate into that model

Rules:

1. Match news records only when they are relevant to the theme.

Use small explicit matching logic:
- entity overlap with theme-linked news entities
- topic overlap with normalized theme title / aliases / primary question tokens if useful
- optional publisher relevance only if it falls naturally out of the fixture and tests

Keep it deterministic and inspectable.
No fuzzy semantic matching.
No embeddings.
No LLMs.

2. If no news records match:
- raise `NewsEvidenceAssemblyError`
- do not invent a packet

3. Matching reasons should be explicit and deterministic, such as:
- `entity_match`
- `topic_match`
- `official_source_match`

4. Only select records that have at least one explicit match reason.

5. Primary record selection should be deterministic:
- official source wins over non-official
- then highest trust score
- then freshest `published_at`
- final tie-break: `article_id` ascending

6. Freshness score:
- compute deterministically from `published_at` age relative to an explicit `reference_time` input
- no hidden current time usage

Suggested buckets:
- <= 2 hours: 1.00
- <= 12 hours: 0.80
- <= 1 day: 0.60
- <= 3 days: 0.35
- > 3 days: 0.15 and add stale flag

7. Trust score:
- packet trust score should be a deterministic aggregation of matched record trust scores
- keep it simple and explicit
- mean is acceptable

8. Coverage score:
- bounded in `[0.0, 1.0]`
- should reflect how well the theme’s linked entities/topics are represented in matched records
- keep it simple and explicit

A reasonable approach:
- count how many linked news entities are observed across matched records
- divide by total linked news entities
- if no linked news entities exist in the theme packet, raise `NewsEvidenceAssemblyError`

9. Official source presence:
- `True` if any matched record has `is_official_source == True`

10. Flags:
Surface explicit flags for cases like:
- `stale_news_evidence`
- `weak_news_trust`
- `weak_news_coverage`
- `official_source_present`
- `single_source_only`
- `single_article_match`

11. Explanation:
Produce a short deterministic explanation string summarizing:
- matched article count
- primary article id
- freshness / trust / coverage scores
- official-source presence
- key flags

## Scoring requirements
Create small pure functions in `scoring.py`.

Suggested functions:
- `compute_news_freshness_score(...)`
- `compute_news_trust_score(...)`
- `compute_news_coverage_score(...)`

Keep them:
- deterministic
- bounded
- easy to inspect
- free of side effects

No randomization.
No hidden global time.
No network assumptions.

## Test requirements

### `test_news_evidence_models.py`
Cover:
- valid packet models
- invalid bounded scores rejected
- required fields enforced

### `test_news_evidence_assembler.py`
Cover:
- linked news records selected correctly
- unmatched records excluded
- no matches raises `NewsEvidenceAssemblyError`
- no linked news entities raises `NewsEvidenceAssemblyError`
- primary record selection deterministic
- coverage score deterministic
- stale / weak-coverage / official-source flags surface correctly
- explanation string deterministic

### `test_news_evidence_scoring.py`
Cover:
- freshness score buckets
- trust score bounded in `[0,1]`
- coverage score bounded in `[0,1]`
- deterministic outputs for known inputs

## Fixtures
Create a small deterministic fixture set with at least:
- one official-source record
- one wire record
- one newsroom or analysis record
- one unrelated record that must be ignored
- timestamps that allow at least one stale case in tests

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement contradiction analysis or reasoning in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/news_evidence/*` exists with the files listed above
2. typed models validate correctly
3. assembler consumes `ThemeLinkPacket` + normalized news records
4. only linked news-relevant records are included
5. deterministic primary record selection works
6. freshness / trust / coverage scores are deterministic and bounded
7. explicit flags surface correctly
8. tests pass
9. no unrelated modules were modified
10. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new news evidence module if mypy is already in use

At minimum, run:
- targeted pytest for the new news evidence tests
- narrow ruff check for touched files
- narrow mypy check for the new news evidence module

## Final output format
Return only:
1. concise summary
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. any deviations from spec
6. explicit note whether `src/polymarket_arb/*` was untouched

List only the final successful validation commands once in section 3.
Mention earlier failed runs only in section 4 if they occurred.

Do not widen the phase.
Do not start reasoning or policy.
Do not start mixed-family comparison updates.
Complete only this bounded phase.
