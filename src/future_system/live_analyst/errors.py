"""Explicit error contracts for the bounded live analyst transport layer."""

from __future__ import annotations


class LiveAnalystError(ValueError):
    """Base error for live analyst boundary failures."""


class LiveAnalystTimeoutError(LiveAnalystError):
    """Raised when live analyst transport exceeds configured timeout."""


class LiveAnalystTransportError(LiveAnalystError):
    """Raised when transport fails or returns malformed/incomplete responses."""
