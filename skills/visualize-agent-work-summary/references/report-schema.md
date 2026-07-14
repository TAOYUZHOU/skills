# Agent Work Summary Payload

The renderer accepts UTF-8 JSON with `schema_version: 1`.

## Minimal example

```json
{
  "schema_version": 1,
  "lang": "zh-CN",
  "title": "Project · Phase 0 → 3",
  "subtitle": "Evidence-backed engineering retrospective",
  "updated_at": "2026-07-14T00:00:00Z",
  "summary": {
    "status": "in_progress",
    "headline": "The state migration is complete; the live baseline is still running.",
    "narrative": "Runtime readiness and benchmark success are reported separately.",
    "metrics": [
      {"value": "3/4", "label": "phases complete", "detail": "Phase 3 is live"}
    ]
  },
  "phases": [
    {
      "id": 0,
      "label": "Freeze the failure",
      "status": "done",
      "purpose": "Make the bug replayable.",
      "outcome": "A deterministic fixture now reproduces the incident.",
      "work": ["Captured the terminal state and its source hashes."],
      "solved": ["Removed ambiguity about the triggering sequence."],
      "achievements": ["Replay runs without a provider call."],
      "caveats": ["The fixture proves this incident, not every future failure."],
      "evidence": [
        {"label": "Fixture summary", "path": "../evidence/phase0/summary.json", "note": "Hash and replay counts"}
      ]
    }
  ],
  "principles": [
    {"title": "One truth source", "body": "Claims must resolve to durable evidence."}
  ],
  "current_state": {
    "headline": "What is true now",
    "facts": ["Three phases are complete."],
    "open_gaps": ["The final live run is not complete."],
    "next_steps": ["Finish the run and regenerate this report."]
  },
  "sources": [
    {"label": "Handoff SSOT", "path": "../handoff.md", "note": "Current project truth"}
  ]
}
```

## Field rules

- Required root fields: `schema_version`, `title`, `summary`, `phases`.
- `summary.status` and every `phases[].status` must be `done`, `in_progress`, `pending`, or `blocked`.
- `phases[].id` must be unique. Numeric IDs are displayed as `PHASE NN`.
- `work`, `solved`, `achievements`, `caveats`, `facts`, `open_gaps`, and `next_steps` are arrays of plain strings.
- `evidence` and `sources` contain `{label, path, note}`. `label` and `path` are required; `note` is optional.
- `summary.metrics` contains `{value, label, detail}`. `value` and `label` are required.
- `principles` contains `{title, body}`.
- Unknown fields are ignored so producers can retain domain-specific source data without changing the renderer.

## Evidence semantics

- A test, manifest, ledger, commit, or structured report may support an engineering claim.
- A provider sandbox pass does not prove benchmark quality.
- A benchmark score must retain its metric, direction, baseline/reference, and evaluation provenance in the underlying evidence.
- Missing or contradictory evidence requires `in_progress`, `pending`, or `blocked`; do not solve uncertainty with more confident prose.
