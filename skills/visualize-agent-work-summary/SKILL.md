---
name: visualize-agent-work-summary
description: Build an evidence-backed, human-friendly standalone HTML path tree from an agent project, iteration roadmap, migration, incident recovery, or multi-phase run. Use when the user asks for a visual work summary, phase-by-phase retrospective, roadmap progress page, long HTML report, agent achievement report, or a clear explanation of what changed, what was solved, what remains, and which files or tests prove each claim.
---

# Visualize Agent Work Summary

Turn verified work facts into a readable long-form path tree. Keep the source payload and generated HTML together so the report is reproducible and easy to refresh.

## Workflow

1. Establish the truth boundary before writing copy.
   - Prefer the project's handoff/SSOT, delivery contract, test summaries, evidence manifests, and Git history.
   - Read only the evidence needed for the requested scope.
   - Distinguish engineering readiness from task or scientific success.
   - Never infer completion from normal prose, file existence alone, or a process exit alone.

2. Create a schema-version-1 JSON payload.
   - Read [report-schema.md](references/report-schema.md) for the compact schema.
   - Give every phase one of `done`, `in_progress`, `pending`, or `blocked`.
   - Include caveats and open gaps beside achievements, not in a hidden appendix.
   - Use repository-relative evidence paths whenever possible; do not publish secrets or private credentials.

3. Validate and render with the bundled standard-library-only generator.

```bash
python3 scripts/render_agent_work_summary.py \
  --input /path/to/report.json \
  --output /path/to/report/index.html
```

4. Verify the artifact.

```bash
python3 scripts/render_agent_work_summary.py \
  --input /path/to/report.json \
  --output /tmp/agent-work-summary.html \
  --check
```

   - Confirm the command reports `ok: true`.
   - Open the HTML locally when a browser is available and inspect desktop and narrow layouts.
   - Check that the page contains no token, API key, `.env` value, or unintended absolute private path.
   - Confirm unfinished work is visibly marked unfinished.

## Truth And Writing Rules

- Lead with the current truth, not a victory slogan.
- Use “completed” only when cited acceptance evidence exists.
- Treat a live sandbox pass, runtime release, and final benchmark result as different achievement classes.
- Describe failures as retained learning when evidence was preserved; do not relabel them as success.
- Prefer counts and exact invariants over adjectives such as “robust” or “production-ready.”
- Link each important claim to a file, test, manifest, or ledger entry.
- Keep the path chronological, but make the outcome of each phase understandable without reading earlier cards.

## Visual Contract

The generator produces one responsive, offline HTML file with:

- a first-viewport truth summary and status metrics;
- a Phase path rail and a vertical branching tree;
- separate “work,” “problems solved,” “achievements,” “evidence,” and “limits” regions;
- status filters, keyboard-accessible links, print styling, and reduced-motion support;
- first-class pending, blocked, and partial states.

Do not add a frontend framework, remote font, analytics script, or CDN just to render a report. Extend the JSON schema or generator only when a real repeated reporting need cannot be expressed by the existing fields.

## Refreshing A Report

Update the JSON facts first, regenerate the HTML, and rerun `--check`. Do not hand-edit generated HTML because that creates a second truth source.
