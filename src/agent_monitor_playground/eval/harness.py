# src/agent_monitor_playground/eval/harness.py
"""
Evaluation harness.

This module runs the pipeline repeatedly across a set of prompts and produces
summary statistics. It is intended for:
- Batch testing (20–50+ tasks)
- Regression checks (monitor behavior over time)
- Quick inspection of failure mode patterns
- False positive / false negative tracking (later, when labels exist)

The harness is intentionally decoupled from Streamlit.
It calls the same pipeline function that the UI and CLI use.

Design choices:
- The harness treats the RiskReport as serialized data (a plain dict) by using
  report.model_dump(). This makes the harness resilient to internal schema changes.
- The harness does not attempt to “judge the judges”. It simply aggregates signals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
from collections import Counter

from agent_monitor_playground.monitors.failure_modes import FailureMode
from agent_monitor_playground.ui_pipeline import run_pipeline


# ---------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------

@dataclass
class HarnessRunResult:
    """
    Outcome of a single pipeline run inside the harness.

    Fields:
    - run_id:
        Identifier of the run, used to locate run artifacts on disk.
    - prompt:
        Task prompt that was executed.
    - model:
        Model used for the run.
    - report:
        Serialized RiskReport (dictionary form via model_dump()).
    - fired_failure_modes:
        List of failure_mode strings for monitors that fired (risk_score > 0).
    - overall_risk:
        Overall risk for the run (copied from the report for convenience).
    """
    run_id: str
    prompt: str
    model: str
    report: Dict[str, Any]
    fired_failure_modes: List[str]
    overall_risk: float


@dataclass
class HarnessSummary:
    """
    Aggregated statistics across multiple harness runs.

    Fields:
    - total_runs:
        Number of runs executed.
    - runs_with_any_risk:
        Count of runs where at least one monitor fired.
    - failure_mode_counts:
        Frequency of each failure_mode among fired monitors.
    - average_overall_risk:
        Mean of overall_risk values.
    - max_overall_risk:
        Maximum overall risk observed.
    - system_failure_runs:
        Count of runs where a system failure mode fired (judge parse failures, etc.).
    """
    total_runs: int
    runs_with_any_risk: int
    failure_mode_counts: Dict[str, int]
    average_overall_risk: float
    max_overall_risk: float
    system_failure_runs: int


# ---------------------------------------------------------------------
# Harness execution
# ---------------------------------------------------------------------

def run_batch(
    *,
    prompts: Iterable[str],
    model_name: str,
    max_output_tokens: int,
    run_root: str = "runs",
) -> List[HarnessRunResult]:
    """
    Executes a batch of prompts through the pipeline.

    Inputs:
    - prompts:
        Iterable of task prompt strings.
    - model_name:
        Model used for every run in this batch.
    - max_output_tokens:
        Output token limit for the agent call.
    - run_root:
        Directory where run artifacts should be stored.

    Returns:
    - List of HarnessRunResult, one per prompt.
    """
    results: List[HarnessRunResult] = []

    for prompt in prompts:
        run_id, _, report_obj = run_pipeline(
            run_root=run_root,
            task_prompt=prompt,
            model_name=model_name,
            max_output_tokens=int(max_output_tokens),
        )

        # Convert the Pydantic model into plain Python data.
        report = report_obj.model_dump()

        # Fired monitors are already separated in report["fired"].
        fired = report.get("fired") or []
        fired_failure_modes = [r.get("failure_mode", FailureMode.NONE) for r in fired]

        overall_risk = float(report.get("overall_risk", 0.0))

        results.append(
            HarnessRunResult(
                run_id=run_id,
                prompt=prompt,
                model=model_name,
                report=report,
                fired_failure_modes=fired_failure_modes,
                overall_risk=overall_risk,
            )
        )

    return results


# ---------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------

def summarize(results: List[HarnessRunResult]) -> HarnessSummary:
    """
    Aggregates high-level statistics for a set of harness run results.

    This is designed to be used in:
    - Scripts
    - Notebooks
    - CI checks (later)

    Summary outputs are intentionally simple so they are easy to print and compare.
    """
    total_runs = len(results)

    runs_with_any_risk = 0
    overall_risks: List[float] = []
    failure_mode_counts: Counter[str] = Counter()

    # A set of failure modes that indicate monitoring system issues,
    # rather than agent behavior issues.
    system_failure_modes = {
        FailureMode.JUDGE_PARSE_FAILURE,
        FailureMode.MONITOR_ERROR,
        FailureMode.INVALID_MONITOR_OUTPUT,
        FailureMode.TIMEOUT,
        FailureMode.API_ERROR,
    }

    system_failure_runs = 0

    for r in results:
        overall_risks.append(r.overall_risk)

        if r.fired_failure_modes:
            runs_with_any_risk += 1

        # Count failure modes for fired monitors only.
        # This avoids noise from "none" results.
        for fm in r.fired_failure_modes:
            failure_mode_counts[fm] += 1

        # Track whether any system failure mode occurred in this run.
        if any(fm in system_failure_modes for fm in r.fired_failure_modes):
            system_failure_runs += 1

    average_overall_risk = (sum(overall_risks) / total_runs) if total_runs else 0.0
    max_overall_risk = max(overall_risks) if overall_risks else 0.0

    return HarnessSummary(
        total_runs=total_runs,
        runs_with_any_risk=runs_with_any_risk,
        failure_mode_counts=dict(failure_mode_counts),
        average_overall_risk=average_overall_risk,
        max_overall_risk=max_overall_risk,
        system_failure_runs=system_failure_runs,
    )


# ---------------------------------------------------------------------
# Convenience entrypoint
# ---------------------------------------------------------------------

def run_and_summarize(
    *,
    prompts: Iterable[str],
    model_name: str,
    max_output_tokens: int,
    run_root: str = "runs",
) -> Tuple[List[HarnessRunResult], HarnessSummary]:
    """
    Runs a batch and returns both:
    - The per-run results (for inspection)
    - The aggregated summary (for reporting)

    This function is the simplest “one call” entrypoint for the harness.
    """
    results = run_batch(
        prompts=prompts,
        model_name=model_name,
        max_output_tokens=max_output_tokens,
        run_root=run_root,
    )
    summary = summarize(results)
    return results, summary
