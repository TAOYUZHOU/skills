---
name: harp-local-llm-translator-eval
description: Evaluate a local small LLM such as Qwythos 9B as a HARP machine-code translator on real runtime raw outputs. Use this whenever testing whether a local model can convert planner/reviewer/executor raw text into structured facts, check information-transfer fidelity, or measure GPU/load before wiring a local model into HARP repair or audit lanes.
---

# HARP Local LLM Translator Eval

Use this skill to test a local OpenAI-compatible small LLM on real HARP runtime output before trusting it in any workflow.

The intended role is diagnostic and bounded: the model translates raw agent text into structured facts; deterministic code scores parseability and field fidelity. Do not let the small model become a hard scientific gate until repeated evals show stable quality.

## Inputs

- One or more raw HARP output files, usually from `.state/last_agent_output.txt` or `.state/structured_output_raw/*.txt`.
- A local OpenAI-compatible endpoint, usually Qwythos through llama-server at `http://127.0.0.1:8080/v1`.

## Run

```bash
python scripts/evaluate_local_translator.py \
  --input /path/to/.state/last_agent_output.txt \
  --input /path/to/.state/structured_output_raw/example.txt \
  --out /path/to/report.json
```

Useful options:

- `--base-url`: defaults to `http://127.0.0.1:8080/v1`
- `--model`: defaults to `qwythos-q4`
- `--max-chars`: trims very long raw output before sending to the model
- `--max-tokens`: completion budget for translated JSON

The script sends `chat_template_kwargs.enable_thinking=false` because Qwythos-style reasoning models may otherwise spend the whole budget in hidden reasoning before emitting final JSON.

## Report

The JSON report records:

- Source file hashes and deterministic directive parse results
- Local-model translated JSON
- Parse success, directive recall, key-id match, and fabrication penalty
- Request latency, token usage, server timings, and GPU memory/utilization/power samples

Treat high scores as permission to use the model for cheap audit or repair assistance, not as permission to bypass deterministic runtime checks.
