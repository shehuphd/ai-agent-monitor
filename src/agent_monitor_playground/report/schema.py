# src/agent_monitor_playground/report/schema.py
"""
Risk report schema.

This module defines the structure of the final output produced by the monitoring
pipeline. A RiskReport represents the aggregated view of all monitor judgments
for a single agent run.

The report is intended to be:
- Machine-readable (for downstream evaluation and storage).
- Human-readable (for UI presentation and debugging).
- Stable (so monitors can evolve without breaking consumers).

The RiskReport does not contain raw logs or events.
It only contains interpreted monitoring results.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from agent_monitor_playground.monitors.base import MonitorResult


class RiskReport(BaseModel):
    """
    Aggregated risk assessment for a single run.

    Fields:
    - run_id:
        Unique identifier of the run this report refers to.
        This must match the folder name under runs/<run_id>/.

    - overall_risk:
        A single scalar summarizing the run’s risk.
        By convention, this is the maximum risk score emitted by any monitor.
        It is constrained to the range [0.0, 1.0].

    - fired:
        List of MonitorResult objects whose risk_score is greater than zero.
        These are the monitors that actively flagged some issue.

    - all_results:
        List of all MonitorResult objects, including those that did not fire.
        This preserves full transparency for debugging and auditing.
    """

    run_id: str
    overall_risk: float = Field(
        ge=0.0,
        le=1.0,
        description="Maximum risk score across all monitors, in the range [0.0, 1.0].",
    )
    fired: List[MonitorResult]
    all_results: List[MonitorResult]

    @staticmethod
    def from_monitor_results(
        *,
        run_id: str,
        monitor_results: List[MonitorResult],
    ) -> "RiskReport":
        """
        Builds a RiskReport from a list of MonitorResult objects.

        This is the canonical way to construct a RiskReport.
        No other code should manually assemble these fields.

        Aggregation rules:
        - overall_risk:
            If no monitors ran, the risk is 0.0.
            Otherwise, it is the maximum risk_score among all monitors.
            This is intentionally conservative: one severe signal dominates.

        - fired:
            Subset of monitor_results where risk_score > 0.0.
            These are the monitors that raised an alert.

        - all_results:
            Full list of all monitor outputs, including benign ones.
        """

        if not monitor_results:
            overall = 0.0
        else:
            overall = max(result.risk_score for result in monitor_results)

        fired = [result for result in monitor_results if result.risk_score > 0.0]

        return RiskReport(
            run_id=run_id,
            overall_risk=overall,
            fired=fired,
            all_results=monitor_results,
        )
