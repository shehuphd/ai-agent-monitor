# src/agent_monitor_playground/logging/writer.py
"""
JSONL run writer.

This module implements the persistence layer for run logs.

Each run is stored under:
    <run_root>/<run_id>/

With an append-only event log at:
    <run_root>/<run_id>/events.jsonl

Why JSONL:
- Append-only logging is simple and robust.
- Each line is a standalone JSON object (easy to stream, grep, and debug).
- The format works well for replay and run history browsing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Union, Optional, TextIO

from agent_monitor_playground.logging.events import RunEvent


class JsonlRunWriter:
    """
    Append-only writer for a single run.

    Responsibilities:
    - Create the run directory if it does not exist.
    - Append events to events.jsonl.
    - Read back the events for monitor execution and UI history.
    """

    def __init__(self, *, run_root: str, run_id: str) -> None:
        """
        Creates a writer bound to one run.

        Inputs:
        - run_root: Directory where run folders are stored (e.g. "runs").
        - run_id: Unique identifier for the run (folder name under run_root).
        """
        self.run_root = Path(run_root)
        self.run_id = run_id

        # Create runs/<run_id>/ if missing.
        self.run_dir = self.run_root / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Create (or append to) the JSONL event log.
        self.events_path = self.run_dir / "events.jsonl"
        self._fh: TextIO = self.events_path.open("a", encoding="utf-8")

    def write(self, event: Union[RunEvent, dict]) -> None:
        """
        Appends one event to the JSONL log.

        Inputs:
        - event: RunEvent (preferred) or a plain dict matching the event schema.

        Behavior:
        - Writes exactly one JSON object per line.
        - Flushes immediately to reduce the risk of losing logs on crashes.
        """
        if isinstance(event, RunEvent):
            payload = event.model_dump()
        else:
            payload = event

        # Ensure a stable JSON representation.
        line = json.dumps(payload, ensure_ascii=False)

        self._fh.write(line + "\n")
        self._fh.flush()

    def read_all_events(self) -> List[RunEvent]:
        """
        Reads the full event log for this run and returns validated RunEvent objects.

        This is used by:
        - Monitors (to inspect the run history)
        - UI history loading (to reconstruct output and reports)

        If an event line fails to parse or validate, it is skipped rather than raising.
        That keeps the system usable even if a run contains partial corruption.
        """
        events: List[RunEvent] = []

        if not self.events_path.exists():
            return events

        with self.events_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    events.append(RunEvent.model_validate(data))
                except Exception:
                    # Invalid lines are ignored to keep run reading robust.
                    continue

        return events

    def close(self) -> None:
        """
        Closes the underlying file handle.

        Streamlit can execute multiple runs in a single process, so closing the file
        prevents handle leaks during development and repeated execution.
        """
        try:
            self._fh.close()
        except Exception:
            # Close errors are ignored because there is no safe recovery path here.
            pass
