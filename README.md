# AI Agent Monitor

By [Mo Shehu](mailto:mo@shehudev.com)

A small playground for running an AI agent, applying safety monitors and LLM judges, and generating risk reports.

Each run:
1. Executes an agent.
2. Applies multiple monitors.
3. Builds a risk report.
4. Writes everything to disk.
5. Can be viewed in UI or CLI.

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

## Monitor report schema
```
{
  "monitor_id": "instruction-following-judge",
  "failure_mode": "none",
  "risk_score": 0.0,
  "explanation": "..."
}
```
