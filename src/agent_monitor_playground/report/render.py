# src/agent_monitor_playground/report/render.py
"""
Rendering helpers for risk reports.

This module converts structured report objects and monitor results into
UI-friendly representations. It does not perform any computation or scoring.
It only formats already computed data so that:

- Streamlit code stays simple.
- Rendering logic stays consistent.
- Output style can be changed in one place later.

This file should contain only pure formatting functions:
no file I/O, no model calls, no business logic.
"""

from __future__ import annotations

from typing import Any, Dict, List


def render_risk_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produces a simplified, UI-ready version of a RiskReport.

    Input:
    - report:
        Serialized RiskReport (from report.model_dump()).

    Output:
    - Dictionary with predictable, presentation-oriented keys:
        {
            "run_id": str,
            "overall_risk": float,
            "fired_count": int,
            "total_monitors": int,
            "fired": [ ... ],
            "all_results": [ ... ]
        }

    This function does not change semantics.
    It only reorganizes fields for display.
    """
    fired = report.get("fired") or []
    all_results = report.get("all_results") or []

    return {
        "run_id": report.get("run_id"),
        "overall_risk": report.get("overall_risk", 0.0),
        "fired_count": len(fired),
        "total_monitors": len(all_results),
        "fired": fired,
        "all_results": all_results,
    }


def render_monitor_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produces a compact, UI-friendly view of a single MonitorResult.

    Input:
    - result:
        Serialized MonitorResult dictionary.

    Output:
    - Dictionary with standardized keys:
        {
            "monitor_id": str,
            "failure_mode": str,
            "risk_score": float,
            "explanation": str
        }
    """
    return {
        "monitor_id": result.get("monitor_id", "unknown"),
        "failure_mode": result.get("failure_mode", "none"),
        "risk_score": float(result.get("risk_score", 0.0)),
        "explanation": result.get("explanation", ""),
    }


def render_monitor_table(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converts a list of MonitorResult objects into a table-like structure.

    This is suitable for:
    - Streamlit st.dataframe
    - CSV export
    - Simple tabular visualization

    Each row is a flattened representation of a monitor result.
    """
    rows: List[Dict[str, Any]] = []

    for r in results:
        rows.append(render_monitor_result(r))

    return rows


def render_fired_only(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters and renders only monitors that fired (risk_score > 0).

    This is useful for UI panels that focus only on problems,
    not on successful checks.
    """
    fired = []

    for r in results:
        if float(r.get("risk_score", 0.0)) > 0.0:
            fired.append(render_monitor_result(r))

    return fired


def render_summary_text(report: Dict[str, Any]) -> str:
    """
    Produces a short, human-readable summary sentence for a report.

    Example:
        "Overall risk: 0.6. 2 out of 4 monitors fired."

    This is useful for headers, tooltips, or compact views.
    """
    overall_risk = report.get("overall_risk", 0.0)
    fired = report.get("fired") or []
    all_results = report.get("all_results") or []

    return (
        f"Overall risk: {overall_risk:.2f}. "
        f"{len(fired)} out of {len(all_results)} monitors fired."
    )
