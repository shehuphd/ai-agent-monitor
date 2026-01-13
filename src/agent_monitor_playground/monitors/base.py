from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from agent_monitor_playground.logging.events import RunEvent


class MonitorResult(BaseModel):
    monitor_id: str
    failure_mode: str
    risk_score: float = Field(ge=0.0, le=1.0)
    explanation: str


class Monitor(Protocol):
    monitor_id: str

    def evaluate(self, *, run_id: str, events: list[RunEvent], agent_output: str) -> MonitorResult:
        ...
