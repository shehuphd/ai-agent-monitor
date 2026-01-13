"""
Central registry of all failure modes used across monitors and judges.

This file defines the shared vocabulary for:
- System failures (monitor / judge errors)
- Agent behavior failures (instruction following, reasoning quality)
- Safety failures (dangerous or unsafe patterns)

Every monitor and judge should import from here instead of inventing
new failure_mode strings.
"""

from enum import Enum


class FailureMode(str, Enum):
    # ------------------------------------------------------------------
    # No failure
    # ------------------------------------------------------------------
    NONE = "none"

    # ------------------------------------------------------------------
    # System / infrastructure failures
    # These indicate problems with the monitoring system itself,
    # not with the agent being evaluated.
    # ------------------------------------------------------------------
    JUDGE_PARSE_FAILURE = "judge parse failure"
    MONITOR_ERROR = "monitor error"
    INVALID_MONITOR_OUTPUT = "invalid monitor output"
    TIMEOUT = "timeout"
    API_ERROR = "api error"

    # ------------------------------------------------------------------
    # Instruction-following and reasoning failures
    # These describe how the agent failed to follow the task.
    # ------------------------------------------------------------------
    IGNORING_INSTRUCTIONS = "ignoring instructions"
    SUSPICIOUS_GOAL_DEVIATION = "suspicious goal deviation"
    OVERCONFIDENT_BUT_WRONG = "overconfident but wrong reasoning"
    PARTIAL_COMPLIANCE = "partial compliance"
    INCORRECT_RESULT = "incorrect result"

    # ------------------------------------------------------------------
    # Safety and security failures
    # These indicate potentially dangerous or risky content.
    # ------------------------------------------------------------------
    UNSAFE_PATTERN_DETECTED = "unsafe pattern detected"
    DANGEROUS_CODE_GENERATION = "dangerous code generation"
    PRIVILEGE_ESCALATION_RISK = "privilege escalation risk"
    DATA_DESTRUCTION_RISK = "data destruction risk"
    COMMAND_INJECTION_RISK = "command injection risk"

    # ------------------------------------------------------------------
    # Output quality failures
    # These describe structural or formatting problems.
    # ------------------------------------------------------------------
    EMPTY_OUTPUT = "empty output"
    UNPARSABLE_OUTPUT = "unparsable output"
    MALFORMED_JSON = "malformed json"
    TRUNCATED_OUTPUT = "truncated output"
