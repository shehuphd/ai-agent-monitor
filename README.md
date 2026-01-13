# AI Agent Monitor

By [Mo Shehu](mailto:mo@shehudev.com)

A minimal prototype of an output-level monitoring system for large language models. It demonstrates how raw model outputs can be evaluated using multiple independent monitors and converted into a structured safety and alignment risk report.

Each run:
1. Generates a model output from a prompt.
2. Applies multiple independent monitors to that output.
3. Aggregates their results into a structured RiskReport.
4. Persists logs and reports.
5. Exposes results via CLI and UI.

---

## Run the UI

`python -m streamlit run ui/streamlit_app.py`

## Run from CLI

```
python -m agent_monitor_playground.cli \
  --prompt "Tell me a story about dinosaurs." \
  --model gpt-4o-mini \
  --max-tokens 800
```

## Set API key

`export OPENAI_API_KEY="your_key_here"`

## Project layout
```
agent/
  client.py       OpenAI wrapper
  loop.py         One-shot agent execution
  prompts.py      Judge prompts
  tasks.py        Task models
  tools.py        Tool interfaces (future)

monitors/
  rules.py        Static monitors
  llm_judges.py   LLM judges
  failure_modes.py Canonical failure modes

report/
  schema.py       RiskReport model
  render.py       Report rendering helpers

logging/
  writer.py       JSONL logger
  events.py       Event schema

eval/
  harness.py      Batch evaluation
  metrics.py      Metrics

storage/
  db.py           Run storage
  models.py       Storage models

ui_pipeline.py    Shared pipeline for UI and CLI
cli.py            Command-line interface
```

## Core objects
```
Agent → Output
Output → Monitors
Monitors → RiskReport
RiskReport → UI / CLI
```

## Risk report schema

```
{
  "run_id": "...",
  "overall_risk": 0.5,
  "fired": [...],
  "all_results": [...]
}
```

## Current monitors

Implemented monitors include:
- Instruction-following judge (LLM-based)
- Output validity and non-emptiness
- Harmful pattern detection (static rules, e.g. destructive CLI commands)
- Toy rule monitors for testing ensemble behavior

## Monitor report schema

Risk reports are emitted as structured JSON to make them machine-consumable for downstream alerting, dashboards, or evaluation pipelines.

```
{
  "monitor_id": "instruction-following-judge",
  "failure_mode": "none",
  "risk_score": 0.0,
  "explanation": "..."
}
```

