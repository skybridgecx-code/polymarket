"""Correlation identifier types and traceability primitives for future-system records.

Connects future decision, control, and recovery records without any
storage, emission, or transport layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class RecordScope(str, Enum):
    """Domain classification of a future-system record."""

    DECISION = "decision"
    CONTROL = "control"
    RECOVERY = "recovery"
    GOVERNANCE = "governance"


class CorrelationId(BaseModel):
    """Stable identifier linking related records across future-system components.

    Passed as a field on every event and audit record to enable replay-style
    reconstruction of decision paths.  Pure in-memory, no I/O.
    """

    value: str


class TraceLink(BaseModel):
    """Links a single record to its parent correlation context and sequence index.

    Provides the minimum context needed to reconstruct a causal chain of
    future-system records from retained data alone.
    """

    correlation_id: str
    record_scope: RecordScope
    sequence: int
    created_at: datetime
