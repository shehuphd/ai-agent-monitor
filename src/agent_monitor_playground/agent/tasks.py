# src/agent_monitor_playground/agent/tasks.py
"""
Task definitions and helpers.

This module defines what a “task” is in a structured, machine-readable way.
Right now the system mostly passes around raw prompt strings, but tasks give
the monitoring system semantic context about what the agent is supposed to do.

Prompts are text, while tasks are intent. This distinction becomes important when:
- Different monitors should apply to different task types.
- Evaluation rules vary between code, math, and creative writing.
- Batch evaluation and benchmarking are introduced.
"""


from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Task:
    """
    Structured representation of an agent task.

    This object describes:
    - What the agent is being asked to do.
    - What kind of output is expected.
    - Optional constraints that monitors and judges can use.

    Fields:
    - task_id:
        Stable identifier for the task type.
        Example: "code-task", "story-task", "math-task".
    - description:
        Human-readable description of the task category.
    - prompt:
        The actual text prompt sent to the agent.
    - expected_output_type:
        Optional hint about what kind of output is expected.
        Examples: "code", "text", "story", "json".
    - max_words:
        Optional soft constraint used by monitors or judges.
        Particularly useful for stories and explanations.
    - metadata:
        Arbitrary structured data for future extensions
        (difficulty, domain, safety sensitivity, etc.).
    """

    task_id: str
    description: str
    prompt: str
    expected_output_type: Optional[str] = None
    max_words: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------
# Task factory helpers
# These functions create common task shapes without duplicating boilerplate.
# ---------------------------------------------------------------------

def create_text_task(prompt: str) -> Task:
    """
    Creates a generic free-form text generation task.

    This is the default when no special structure is required.
    """
    return Task(
        task_id="text-task",
        description="General text generation task",
        prompt=prompt,
        expected_output_type="text",
    )


def create_story_task(prompt: str, max_words: int = 200) -> Task:
    """
    Creates a short story generation task.

    Story tasks typically:
    - Expect narrative output.
    - Have explicit length constraints.
    """
    return Task(
        task_id="story-task",
        description="Short story generation",
        prompt=prompt,
        expected_output_type="story",
        max_words=max_words,
    )


def create_code_task(prompt: str) -> Task:
    """
    Creates a code generation task.

    Code tasks are safety-sensitive and should trigger:
    - UnsafePatternsMonitor strongly.
    - Additional security-focused judges later.
    """
    return Task(
        task_id="code-task",
        description="Code generation task",
        prompt=prompt,
        expected_output_type="code",
    )


def create_math_task(prompt: str) -> Task:
    """
    Creates a mathematical problem-solving task.

    These tasks emphasize correctness over style or creativity.
    """
    return Task(
        task_id="math-task",
        description="Mathematical problem solving",
        prompt=prompt,
        expected_output_type="text",
    )


# ---------------------------------------------------------------------
# Task serialization helpers
# ---------------------------------------------------------------------

def task_to_prompt(task: Task) -> str:
    """
    Extracts the prompt string from a Task.

    This keeps the agent interface simple:
    the agent only needs text, while monitors and judges
    can access the richer task object.
    """
    return task.prompt
