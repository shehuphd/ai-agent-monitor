# src/agent_monitor_playground/cli.py
"""
Command-line interface for agent-monitor-playground.

The CLI exists so the system isn't just a Streamlit app.
It enables the core pipeline to be usable headlessly.

The CLI should:
- Call the same pipeline logic as the UI
- Never duplicate business logic
- Only handle argument parsing and printing

Typical usage:

Single run:
    python -m agent_monitor_playground.cli run \
        --prompt "Add 2+2" \
        --model gpt-4o-mini \
        --max-output-tokens 200

Batch run (later, when tasks.jsonl is wired):
    python -m agent_monitor_playground.cli batch \
        --tasks data/tasks/seed_tasks.jsonl
"""

import argparse
import json
from pathlib import Path
from typing import Optional

# Import your real pipeline entrypoint.
# This must be the same function Streamlit calls.
from agent_monitor_playground.ui_pipeline import run_pipeline


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def print_run_summary(run_id: str, output: str, report: dict) -> None:
    """
    Pretty-print a minimal run summary to the terminal.
    """
    print("\n================ Run completed ================")
    print(f"Run ID: {run_id}")
    print("\n--- Agent output ---")
    print(output)

    print("\n--- Risk report ---")
    print(json.dumps(report, indent=2))


# ---------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------

def cmd_run(args: argparse.Namespace) -> None:
    """
    Execute a single agent run from CLI arguments.
    """
    run_id, output, report = run_pipeline(
        run_root=args.run_root,
        task_prompt=args.prompt,
        model_name=args.model,
        max_output_tokens=args.max_output_tokens,
    )

    print_run_summary(run_id, output, report.model_dump())


def cmd_batch(args: argparse.Namespace) -> None:
    """
    Placeholder for batch execution.

    This will later:
    - Load tasks from a JSONL file
    - Run each task
    - Aggregate statistics
    """
    tasks_path = Path(args.tasks)
    if not tasks_path.exists():
        raise SystemExit(f"Tasks file not found: {tasks_path}")

    print("Batch mode not implemented yet.")
    print(f"Would run tasks from: {tasks_path}")


def cmd_replay(args: argparse.Namespace) -> None:
    """
    Placeholder for replaying an existing run.

    Later this will:
    - Load an existing run
    - Re-run monitors
    - Compare results
    """
    print("Replay mode not implemented yet.")
    print(f"Would replay run: {args.run_id}")


# ---------------------------------------------------------------------
# Main CLI definition
# ---------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """
    Build the top-level argument parser and subcommands.
    """
    parser = argparse.ArgumentParser(
        prog="agent-monitor-playground",
        description="CLI for running and evaluating coding agents."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -------------------------------
    # run
    # -------------------------------
    run_parser = subparsers.add_parser(
        "run",
        help="Run a single agent task."
    )
    run_parser.add_argument(
        "--prompt",
        required=True,
        help="Task prompt to send to the agent."
    )
    run_parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model name to use."
    )
    run_parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=500,
        help="Maximum number of tokens the agent may generate."
    )
    run_parser.add_argument(
        "--run-root",
        default="runs",
        help="Directory where run artifacts are stored."
    )
    run_parser.set_defaults(func=cmd_run)

    # -------------------------------
    # batch (stub)
    # -------------------------------
    batch_parser = subparsers.add_parser(
        "batch",
        help="Run a batch of tasks from a file (not yet implemented)."
    )
    batch_parser.add_argument(
        "--tasks",
        required=True,
        help="Path to a JSONL file of tasks."
    )
    batch_parser.set_defaults(func=cmd_batch)

    # -------------------------------
    # replay (stub)
    # -------------------------------
    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay and re-score an existing run (not yet implemented)."
    )
    replay_parser.add_argument(
        "--run-id",
        required=True,
        help="ID of the run to replay."
    )
    replay_parser.set_defaults(func=cmd_replay)

    return parser


def main() -> None:
    """
    CLI entrypoint.
    """
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
