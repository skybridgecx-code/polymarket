"""Deterministic news adapter boundary for fixture-based normalization."""

from future_system.news_adapter.filters import (
    apply_news_record_filter,
    filter_news_records,
    normalize_news_filters,
)
from future_system.news_adapter.models import (
    NewsAdapterError,
    NewsAdapterParseResult,
    NewsRecordFilter,
    NewsSource,
    NewsSourceType,
    NormalizedNewsRecord,
    normalize_news_list,
)
from future_system.news_adapter.parser import FixtureNewsAdapter, parse_news_records
from future_system.news_adapter.protocol import NewsAdapterProtocol

__all__ = [
    "FixtureNewsAdapter",
    "NewsAdapterError",
    "NewsAdapterParseResult",
    "NewsAdapterProtocol",
    "NewsRecordFilter",
    "NewsSource",
    "NewsSourceType",
    "NormalizedNewsRecord",
    "apply_news_record_filter",
    "filter_news_records",
    "normalize_news_filters",
    "normalize_news_list",
    "parse_news_records",
]
