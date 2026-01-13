# ui/streamlit_app.py
#
# Streamlit UI entrypoint.
# This file should only contain UI code plus lightweight run loading for history.
# The execution pipeline lives in src/agent_monitor_playground/ui_pipeline.py.

import inspect
import agent_monitor_playground.ui_pipeline as up
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import streamlit as st

from agent_monitor_playground.ui_pipeline import run_pipeline



def load_run_from_disk(run_root: str, run_id: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Loads the last agent output text and the last risk report from runs/<run_id>/events.jsonl.
    """
    events_path = Path(run_root) / run_id / "events.jsonl"
    if not events_path.exists():
        return None, None

    output_text: Optional[str] = None
    report: Optional[Dict[str, Any]] = None

    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            e = json.loads(line)
            event_type = e.get("event_type")
            payload = e.get("payload") or {}

            if event_type == "agent_output":
                output_text = payload.get("text")
            elif event_type == "risk_report":
                report = payload

    return output_text, report


st.set_page_config(page_title="Agent monitor playground", layout="wide")
st.title("Agent monitor playground")
st.write("Click run to execute an agent → monitors → report pipeline.")

col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    # Run history panel
    st.subheader("Run history")

    run_root_for_history = st.session_state.get("run_root_last", "runs")
    runs_path = Path(run_root_for_history)

    run_ids = []
    if runs_path.exists():
        run_ids = sorted(
            [p.name for p in runs_path.iterdir() if p.is_dir()],
            key=lambda rid: (runs_path / rid).stat().st_mtime,
            reverse=True,
        )

    selected_run = st.selectbox(
        "Load a previous run",
        options=["(latest)"] + run_ids[:25],
        index=0,
    )

    if st.button("Load selected run"):
        rid = run_ids[0] if selected_run == "(latest)" and run_ids else selected_run
        if rid and rid != "(latest)":
            out, rep = load_run_from_disk(run_root_for_history, rid)
            if out is not None:
                st.session_state["last_run_id"] = rid
                st.session_state["last_output"] = out
            if rep is not None:
                st.session_state["last_report"] = rep

    st.divider()

    # Run form
    with st.form("run_form", clear_on_submit=False):
        run_root = st.text_input("Runs folder", value="runs")

        task_prompt = st.text_area(
            "Task prompt",
            value="Say hello.",
            height=140,
            help="This text is passed into the pipeline as the task prompt.",
        )

        model_name = st.text_input(
            "Model name",
            value="gpt-4o-mini",
            help="Model used for the agent run.",
        )

        max_output_tokens = st.number_input(
            "Max output tokens",
            min_value=50,
            max_value=4000,
            value=1200,
            step=50,
        )

        submitted = st.form_submit_button("Run", type="primary")

    if submitted:
        run_id, out, report = run_pipeline(
            run_root=run_root,
            task_prompt=task_prompt,
            model_name=model_name,
            max_output_tokens=int(max_output_tokens),
        )

        st.session_state["last_run_id"] = run_id
        st.session_state["last_output"] = out
        st.session_state["last_report"] = report.model_dump()
        st.session_state["run_root_last"] = run_root


with col_right:
    run_id = st.session_state.get("last_run_id")

    if not run_id:
        st.info("No run yet.")
    else:
        st.subheader("Output")

        view_mode = st.radio(
            "Output view",
            ["Rendered", "Raw"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if view_mode == "Rendered":
            st.markdown(st.session_state["last_output"])
        else:
            st.text_area(
                label="",
                value=st.session_state["last_output"],
                height=320,
                disabled=True,
                label_visibility="collapsed",
            )

        st.subheader("Risk report")
        st.json(st.session_state["last_report"])


# Auto-load latest run on first page load (optional convenience)
if "last_run_id" not in st.session_state:
    run_root = st.session_state.get("run_root_last", "runs")
    runs_path = Path(run_root)
    if runs_path.exists():
        run_ids = sorted(
            [p.name for p in runs_path.iterdir() if p.is_dir()],
            key=lambda rid: (runs_path / rid).stat().st_mtime,
            reverse=True,
        )
        if run_ids:
            out, rep = load_run_from_disk(run_root, run_ids[0])
            if out is not None:
                st.session_state["last_run_id"] = run_ids[0]
                st.session_state["last_output"] = out
            if rep is not None:
                st.session_state["last_report"] = rep
