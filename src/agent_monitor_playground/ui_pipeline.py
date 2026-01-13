"""
Execution pipeline for a single agent run.

This module contains the core orchestration logic:
- Create a run
- Log all events
- Call the agent
- Run monitors
- Build a risk report

It is intentionally UI-agnostic and CLI-agnostic.
Both Streamlit and the CLI import and call this module.
"""

import uuid

from agent_monitor_playground.logging.events import RunEvent, now_iso
from agent_monitor_playground.logging.writer import JsonlRunWriter
from agent_monitor_playground.agent.loop import run_one_shot
from agent_monitor_playground.report.schema import RiskReport
from agent_monitor_playground.monitors.rules import EmptyOutputMonitor, UnsafePatternsMonitor
from agent_monitor_playground.monitors.llm_judges import InstructionFollowingJudge, DestructiveIntentJudge


def run_pipeline(
    *,
    run_root: str,
    task_prompt: str,
    model_name: str,
    max_output_tokens: int,
):
    """
    Executes a full agent → monitors → report cycle.

    Returns:
        run_id: str
        agent_output: str
        report: RiskReport
    """

    run_id = str(uuid.uuid4())
    writer = JsonlRunWriter(run_root=run_root, run_id=run_id)

    # Log task start
    writer.write(
        RunEvent(
            ts=now_iso(),
            run_id=run_id,
            event_type="task_started",
            payload={
                "prompt": task_prompt,
            },
        )
    )

    # Log agent prompt
    writer.write(
        RunEvent(
            ts=now_iso(),
            run_id=run_id,
            event_type="agent_prompt",
            payload={
                "prompt": task_prompt,
                "model": model_name,
                "max_output_tokens": int(max_output_tokens),
            },
        )
    )

    # Run the agent
    agent_result = run_one_shot(
        prompt=task_prompt,
        model=model_name,
        max_output_tokens=max_output_tokens,
    )

    agent_output = agent_result.text

    # Log agent output
    writer.write(
        RunEvent(
            ts=now_iso(),
            run_id=run_id,
            event_type="agent_output",
            payload={
                "text": agent_output,
                "model": agent_result.model,
                "latency_ms": agent_result.latency_ms,
                "usage": agent_result.usage,
                "finish_reason": getattr(agent_result, "finish_reason", None),
            },
        )
    )

    # Monitors
    monitors = [
        EmptyOutputMonitor(),
        # HelloWorldMonitor(),
        UnsafePatternsMonitor(),           # output-level static scan
        InstructionFollowingJudge(model=model_name),
        DestructiveIntentJudge(model=model_name),   # intent-level evaluation
    ]


    run_log = writer.read_all_events()
    monitor_results = []

    for monitor in monitors:
        result = monitor.evaluate(
            run_id=run_id,
            events=run_log,
            agent_output=agent_output,
        )
        monitor_results.append(result)

        writer.write(
            RunEvent(
                ts=now_iso(),
                run_id=run_id,
                event_type="monitor_result",
                payload=result.model_dump(),
            )
        )

    # Build risk report
    report = RiskReport.from_monitor_results(
        run_id=run_id,
        monitor_results=monitor_results,
    )

    writer.write(
        RunEvent(
            ts=now_iso(),
            run_id=run_id,
            event_type="risk_report",
            payload=report.model_dump(),
        )
    )

    writer.close()
    return run_id, agent_output, report
