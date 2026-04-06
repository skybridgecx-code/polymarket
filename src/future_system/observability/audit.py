"""Immutable audit-record contracts for future-system attribution.

Records who acted, what was decided, when, and by which governance role.
No persistence or external calls — pure in-memory contract only.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from future_system.observability.correlation import TraceLink


class DecisionKind(str, Enum):
    """Nature of a future-system governance or control decision."""

    APPROVAL = "approval"
    DENIAL = "denial"
    HOLD = "hold"
    ESCALATION = "escalation"
    OVERRIDE = "override"


class AuditRecord(BaseModel):
    """Immutable attribution record for a single future-system decision.

    Captures who acted, what was decided, when, and by which governance role.
    This is the in-memory contract — not a persistence layer.  All fields
    are required so that incomplete records cannot be silently created.
    """

    record_id: str
    actor: str
    action: str
    granted_by: str
    decided_at: datetime
    trace: TraceLink
    decision_kind: DecisionKind
    rationale: str
