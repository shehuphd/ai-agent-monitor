# src/agent_monitor_playground/agent/types.py
"""
This file defines all *agent-level* data structures.

These types describe:
- What the agent receives as input.
- What the agent returns as output.
- How tool calls are represented.

They do NOT describe:
- Monitor results
- Risk reports
- Judge outputs
Those live under the monitors/ and report/ folders.

Think of this file as the contract between:
UI → Agent → Pipeline.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import time


# -------------------------------------------------------------------
# Agent input
# -------------------------------------------------------------------

@dataclass
class AgentRequest:
    """
    Represents a single request sent to the agent.

    This is built from the Streamlit form and passed into your loop.
    """
    prompt: str                 # The task prompt entered by the user
    model: str                  # The model name (e.g. "gpt-4o-mini")
    max_output_tokens: int      # Output token limit for the model
    temperature: float = 0.0    # Optional. Default is deterministic output


# -------------------------------------------------------------------
# Agent output
# -------------------------------------------------------------------

@dataclass
class AgentResponse:
    """
    Represents the raw result returned by the agent after a model call.

    This is what the monitors consume.
    """
    text: str                   # Final text output from the model
    model: str                  # Model that produced the response
    latency_ms: float           # Time spent waiting on the model
    usage: Optional[Dict[str, int]] = None
    # usage example:
    # {
    #   "prompt_tokens": 123,
    #   "completion_tokens": 456,
    #   "total_tokens": 579
    # }

    finish_reason: Optional[str] = None
    # finish_reason examples:
    # "stop", "length", "content_filter"

    raw: Optional[Any] = None
    # raw holds the unprocessed API response object.
    # Useful for debugging and future extensions.


# -------------------------------------------------------------------
# Tool calling (even if you are not using tools yet)
# -------------------------------------------------------------------

@dataclass
class ToolCall:
    """
    Represents a request made by the model to call a tool.

    Example:
    {
        "name": "search_web",
        "arguments": {"query": "weather in London"}
    }
    """
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """
    Represents the result returned by a tool back to the agent.
    """
    name: str
    output: Any
    success: bool = True
    error: Optional[str] = None


# -------------------------------------------------------------------
# Run-time metadata
# -------------------------------------------------------------------

@dataclass
class RunMetadata:
    """
    Lightweight metadata describing a run.

    This is useful for run history panels and indexing.
    """
    run_id: str
    created_at: float = field(default_factory=lambda: time.time())
    model: Optional[str] = None
    prompt_preview: Optional[str] = None
    # prompt_preview is a short truncated version of the task prompt
    # shown in dropdowns like:
    # "Add 2+2"
    # "Tell me a story about dinosaurs"


# -------------------------------------------------------------------
# Helper constructors
# -------------------------------------------------------------------

def make_agent_response(
    *,
    text: str,
    model: str,
    start_time: float,
    end_time: float,
    usage: Optional[Dict[str, int]] = None,
    finish_reason: Optional[str] = None,
    raw: Optional[Any] = None,
) -> AgentResponse:
    """
    Small helper to build an AgentResponse while automatically computing latency.
    """
    latency_ms = (end_time - start_time) * 1000.0

    return AgentResponse(
        text=text,
        model=model,
        latency_ms=latency_ms,
        usage=usage,
        finish_reason=finish_reason,
        raw=raw,
    )
