# src/agent_monitor_playground/agent/tools.py
"""
Tool interface definitions.

This module defines the contract for tools that an agent may call during
execution. Even if no tools are implemented yet, this file establishes the
shape of the system so that tool use can be added without refactoring the
agent loop.

Tools are external capabilities the agent can invoke, such as:
- Reading or writing files
- Running safe shell commands
- Making HTTP requests
- Querying databases

This file does NOT implement any real tools yet. It only defines:
- How tools are described
- How tool calls are represented
- How a tool registry is structured
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


# ---------------------------------------------------------------------
# Tool specification
# ---------------------------------------------------------------------

@dataclass
class ToolSpec:
    """
    Describes a single tool that the agent can call.

    Fields:
    - name:
        Unique identifier used by the agent to refer to the tool.
    - description:
        Short explanation of what the tool does.
    - args_schema:
        Optional JSON-schema-like dictionary describing the expected arguments.
        This is used later when exposing tools to the model.
    """

    name: str
    description: str
    args_schema: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------
# Tool call and result representations
# ---------------------------------------------------------------------

@dataclass
class ToolCall:
    """
    Represents a request from the agent to invoke a tool.

    This object is usually created after parsing a model response that
    indicates a tool should be called.

    Fields:
    - name:
        Name of the tool being invoked.
    - arguments:
        Dictionary of arguments passed to the tool.
    """

    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """
    Represents the result of executing a tool.

    Fields:
    - name:
        Name of the tool that was executed.
    - output:
        The tool's return value.
    - success:
        Whether the tool completed successfully.
    - error:
        Optional error message if execution failed.
    """

    name: str
    output: Any
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------

class ToolRegistry:
    """
    Registry mapping tool names to Python callables.

    This object allows the agent loop to:
    - Look up a tool by name.
    - Execute it with validated arguments.
    - Return results in a consistent format.

    It also provides a single place to control:
    - Which tools are exposed to the agent.
    - Which tools are considered safe.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._specs: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec, func: Callable[..., Any]) -> None:
        """
        Registers a new tool.

        Inputs:
        - spec:
            ToolSpec describing the tool.
        - func:
            Python callable implementing the tool logic.
        """
        self._tools[spec.name] = func
        self._specs[spec.name] = spec

    def get_spec(self, name: str) -> Optional[ToolSpec]:
        """
        Returns the ToolSpec for a given tool name, if it exists.
        """
        return self._specs.get(name)

    def list_specs(self) -> Dict[str, ToolSpec]:
        """
        Returns all registered ToolSpec objects.

        This is what will later be passed to the model so it knows
        which tools are available.
        """
        return dict(self._specs)

    def execute(self, call: ToolCall) -> ToolResult:
        """
        Executes a tool call and wraps the result in a ToolResult.

        If the tool name is unknown or execution fails, the error
        is captured and returned instead of raising.
        """
        if call.name not in self._tools:
            return ToolResult(
                name=call.name,
                output=None,
                success=False,
                error=f"Unknown tool: {call.name}",
            )

        func = self._tools[call.name]
        try:
            result = func(**call.arguments)
            return ToolResult(
                name=call.name,
                output=result,
                success=True,
            )
        except Exception as e:
            return ToolResult(
                name=call.name,
                output=None,
                success=False,
                error=str(e),
            )


# ---------------------------------------------------------------------
# Default empty registry
# ---------------------------------------------------------------------

def create_empty_registry() -> ToolRegistry:
    """
    Creates a ToolRegistry with no registered tools.

    This is the default state of the system:
    - The agent is allowed to run.
    - No external side effects are possible.
    - All tool calls would fail safely.

    It provides a clean starting point for future tool integration.
    """
    return ToolRegistry()
