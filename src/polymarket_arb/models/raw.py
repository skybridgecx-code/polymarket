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


class RawClobFeeRate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: Literal["clob.fee_rate"]
    fetched_at: datetime
    token_id: str
    payload: dict[str, Any]


class RawDataLeaderboardEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: Literal["data_api.leaderboard"]
    fetched_at: datetime
    time_period: str
    order_by: str
    payload: dict[str, Any]


class RawDataTopHolderGroup(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: Literal["data_api.holders"]
    fetched_at: datetime
    condition_ids: list[str]
    payload: dict[str, Any]


class RawDataUserActivity(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: Literal["data_api.activity"]
    fetched_at: datetime
    wallet_address: str
    payload: dict[str, Any]


class RawWsMarketMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: Literal["ws.market"]
    received_at: datetime
    payload: dict[str, Any]
