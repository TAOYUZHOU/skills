---
name: breakpoint-update-orchestrator
description: Decide and execute safe breakpoint updates for long-running agent or ML job queues when external information, data, mechanisms, prompts, or task assumptions change. Use when Codex needs to stop new jobs, let valid running jobs drain, trigger a local Codex/Cursor/update agent, and restart or requeue work without wasting already-valid computation.
---

# Breakpoint Update Orchestrator

Use this skill when a long-running queue is already active and a material update arrives: new data, corrected labels, mechanism changes, prompt changes, new experimental requirements, or a bug that affects future runs.

The goal is to decide whether to stop immediately, drain to a safe boundary, or defer, then implement that decision with a reproducible guard.

## Decision Model

Classify the update first:

- **Invalidates current running jobs**: corrupt data, wrong split, wrong target, wrong mechanism, unsafe code. Stop immediately or at least prevent results from entering final reports.
- **Invalidates only future jobs**: new ablation, better scheduler, changed report format, new priority. Block new launches, let current valid jobs finish, then update.
- **Improves efficiency only**: scheduling, logging, monitoring, minor report metadata. Apply at the next natural queue boundary.
- **Cosmetic/report-only**: no need to stop training; update post-processing.

Recommended breakpoints:

- **Immediate stop**: current outputs would be scientifically invalid.
- **Drain active workers**: active jobs are still valid, but pending jobs should use updated code/data/plan.
- **Batch boundary**: finish current seed, model family, or job class before updating.
- **Post-run only**: update report builder or documentation after training.

## Guard Workflow

1. Identify launcher processes and worker processes.
2. Create a block marker that cooperative runners can check before launching new jobs.
3. For non-cooperative launchers, optionally freeze only the launcher process with `SIGSTOP`; do not freeze worker/train processes.
4. Poll worker processes until they finish naturally.
5. Trigger update commands, such as a local Codex app server call, Cursor agent command, shell script, or queue restart.
6. Write a status JSONL trail.

## Quick Start

Dry-run process matching first:

```bash
python3 scripts/breakpoint_guard.py \
  --worker-pattern 'train_hydrolysis_multitask|train_foundation_multitask' \
  --launcher-pattern 'run_v19_strict_science_matrix_parallel' \
  --block-file /tmp/science_matrix.NO_NEW_JOBS \
  --status-jsonl /tmp/breakpoint_update.status.jsonl \
  --dry-run
```

Drain active workers and freeze only the launcher:

```bash
python3 scripts/breakpoint_guard.py \
  --worker-pattern 'train_hydrolysis_multitask|train_foundation_multitask' \
  --launcher-pattern 'run_v19_strict_science_matrix_parallel' \
  --mode freeze-launchers \
  --block-file /tmp/science_matrix.NO_NEW_JOBS \
  --status-jsonl /tmp/breakpoint_update.status.jsonl \
  --poll-sec 30 \
  --on-ready 'cd /path/to/workspace && codex exec "apply the pending update and restart the queue"'
```

Use `assets/breakpoint_config_template.json` for a config-driven invocation and `assets/cron_poll_template.sh` for cron/systemd-style polling.

For a runner that already supports a lock file, set `mode` to `cooperative` and make the runner check the block file before each new launch. For a runner that does not yet support that protocol, set `mode` to `freeze-launchers` so the guard freezes only the queue launcher while allowing already-started training processes to finish.

Read `references/breakpoint_policy.md` when deciding whether the new information invalidates active jobs, future jobs only, or post-processing only.

## Safety Rules

- Prefer drain over kill when active jobs remain scientifically valid.
- Do not kill worker processes unless the update invalidates their outputs.
- Do not rely only on process names; record the exact patterns used.
- Write a status JSONL and a block marker before changing launcher behavior.
- If the runner supports a cooperative lock file, use that before signals.
- If using `SIGSTOP`, freeze launcher processes only; leave training workers running.
- Remove or rotate block files only after the update agent has restarted the queue intentionally.
