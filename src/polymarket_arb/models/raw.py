from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class RawGammaEvent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: Literal["gamma.events"]
    fetched_at: datetime
    payload: dict[str, Any]


class RawClobBook(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: Literal["clob.book"]
    fetched_at: datetime
    token_id: str
    payload: dict[str, Any]

