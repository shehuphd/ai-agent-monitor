from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunEvent(BaseModel):
    ts: str
    run_id: str
    event_type: Literal[
        "task_started",
        "agent_prompt",
        "agent_output",
        "monitor_result",
        "risk_report",
        "debug monitors",
    ]
    payload: dict[str, Any]
