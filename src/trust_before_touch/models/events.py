from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
