# src/agent_monitor_playground/eval/metrics.py
"""
Evaluation metrics.

This module defines reusable metric calculations for evaluating monitor output.

The harness (eval/harness.py) is responsible for running tasks and collecting
per-run results.

This module is responsible for turning those results into numbers, such as:
- How often monitors fire
- Which failure modes are most common
- How many runs are affected by system failures
- Basic false positive / false negative metrics (when ground truth exists)

This file intentionally contains pure functions, with:
- No I/O
- No Streamlit code
- No pipeline execution
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from collections import Counter, defaultdict

from agent_monitor_playground.monitors.failure_modes import FailureMode


# ---------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------

@dataclass
class BasicCounts:
    """
    Basic counts computed from a batch of runs.

    Fields:
    - total_runs:
        Number of runs analyzed.
    - runs_with_any_risk:
        Runs where at least one monitor fired (risk_score > 0).
    - failure_mode_counts:
        Frequency of each failure mode among fired monitors.
    - monitor_fire_counts:
        Frequency of each monitor_id firing at least once per run.
    """
    total_runs: int
    runs_with_any_risk: int
    failure_mode_counts: Dict[str, int]
    monitor_fire_counts: Dict[str, int]


@dataclass
class ConfusionMatrix:
    """
    Confusion matrix for a binary classification problem.

    This is used once ground truth labels exist.

    Fields:
    - tp: true positives
    - fp: false positives
    - tn: true negatives
    - fn: false negatives
    """
    tp: int
    fp: int
    tn: int
    fn: int

    def precision(self) -> float:
        denom = self.tp + self.fp
        return (self.tp / denom) if denom else 0.0

    def recall(self) -> float:
        denom = self.tp + self.fn
        return (self.tp / denom) if denom else 0.0

    def f1(self) -> float:
        p = self.precision()
        r = self.recall()
        denom = p + r
        return (2 * p * r / denom) if denom else 0.0


# ---------------------------------------------------------------------
# Core metrics (no ground truth required)
# ---------------------------------------------------------------------

def compute_basic_counts(reports: Iterable[Dict[str, Any]]) -> BasicCounts:
    """
    Computes basic frequency metrics from a set of serialized risk reports.

    Input:
    - reports:
        Iterable of RiskReport-like dicts (from report.model_dump()).

    Output:
    - BasicCounts with:
        - overall run counts
        - failure mode frequencies
        - per-monitor fire frequencies

    Expected report structure:
    - report["fired"] is a list of monitor result dicts
    - each monitor result contains:
        - "monitor_id"
        - "failure_mode"
        - "risk_score"
    """
    reports_list = list(reports)
    total_runs = len(reports_list)

    runs_with_any_risk = 0
    failure_mode_counts: Counter[str] = Counter()
    monitor_fire_counts: Counter[str] = Counter()

    for report in reports_list:
        fired = report.get("fired") or []

        if fired:
            runs_with_any_risk += 1

        # Count failure modes and monitor fire frequency.
        # A monitor contributes at most +1 per run for monitor_fire_counts.
        seen_monitors: Set[str] = set()

        for r in fired:
            monitor_id = str(r.get("monitor_id", "unknown"))
            failure_mode = str(r.get("failure_mode", FailureMode.NONE))
            failure_mode_counts[failure_mode] += 1

            if monitor_id not in seen_monitors:
                monitor_fire_counts[monitor_id] += 1
                seen_monitors.add(monitor_id)

    return BasicCounts(
        total_runs=total_runs,
        runs_with_any_risk=runs_with_any_risk,
        failure_mode_counts=dict(failure_mode_counts),
        monitor_fire_counts=dict(monitor_fire_counts),
    )


def system_failure_rate(reports: Iterable[Dict[str, Any]]) -> float:
    """
    Computes the fraction of runs that include any system-level failure.

    System failures indicate monitoring infrastructure issues, such as:
    - judge parse failure
    - monitor exception
    - timeout

    This metric helps distinguish agent misbehavior from monitor instability.
    """
    system_failure_modes = {
        FailureMode.JUDGE_PARSE_FAILURE,
        FailureMode.MONITOR_ERROR,
        FailureMode.INVALID_MONITOR_OUTPUT,
        FailureMode.TIMEOUT,
        FailureMode.API_ERROR,
    }

    reports_list = list(reports)
    if not reports_list:
        return 0.0

    system_failure_runs = 0

    for report in reports_list:
        fired = report.get("fired") or []
        fired_modes = {str(r.get("failure_mode", "")) for r in fired}
        if any(mode in system_failure_modes for mode in fired_modes):
            system_failure_runs += 1

    return system_failure_runs / len(reports_list)


# ---------------------------------------------------------------------
# Metrics requiring ground truth labels (optional, later)
# ---------------------------------------------------------------------

def confusion_matrix_for_mode(
    *,
    reports: Iterable[Dict[str, Any]],
    truth_labels: Dict[str, bool],
    target_failure_mode: str,
) -> ConfusionMatrix:
    """
    Computes a confusion matrix for whether a specific failure mode occurred.

    Inputs:
    - reports:
        Iterable of serialized reports.
    - truth_labels:
        Mapping from run_id -> bool indicating whether the target failure mode
        truly occurred (human-labeled ground truth).
    - target_failure_mode:
        Failure mode string to evaluate.

    Output:
    - ConfusionMatrix

    Assumptions:
    - truth_labels contains entries for the run_ids being evaluated.
    - If a run_id is missing from truth_labels, it is skipped.
    """
    tp = fp = tn = fn = 0

    for report in reports:
        run_id = str(report.get("run_id", ""))
        if run_id not in truth_labels:
            continue

        fired = report.get("fired") or []
        predicted = any(str(r.get("failure_mode", "")) == target_failure_mode for r in fired)
        actual = bool(truth_labels[run_id])

        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and not actual:
            tn += 1
        else:
            fn += 1

    return ConfusionMatrix(tp=tp, fp=fp, tn=tn, fn=fn)
