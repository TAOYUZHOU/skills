---
name: resource-aware-queue-scheduler
description: Use when scheduling many independent local shell or Python jobs under CPU/GPU/memory limits, especially ML training matrices. Helps run smoke profiling, estimate per-task resource peaks, solve a resource-constrained parallel plan, and run an adaptive queue from JSON job definitions.
metadata:
  short-description: Profile and adaptively schedule CPU/GPU job queues
---

# Resource-Aware Queue Scheduler

Use this skill for independent local jobs where the user wants high throughput while respecting CPU, GPU utilization, and GPU memory limits. It is intended for shell/Python training matrices, ablation queues, benchmark sweeps, and other resumable job lists.

## Queue Contract

The scripts accept a JSON file with:

```json
{
  "jobs": [
    {
      "job_id": "unique_name",
      "cmd": ["python", "train.py", "--epochs", "120"],
      "out_dir": "/path/to/output",
      "done_file": "run_config.json"
    }
  ]
}
```

See `references/config_schema.md` for the full schema and `assets/queue_template.json` for a minimal template.

## Workflow

1. Confirm no conflicting runner is active, or stop the old runner cleanly.
2. Profile representative job classes with short smoke runs:

```bash
python scripts/profile_queue.py \
  --queue /path/to/queue.json \
  --profile-out /path/to/resource_profiles.json \
  --work-dir /path/to/workspace \
  --profile-root /path/to/profile_outputs \
  --group-regex '^(scratch|foundation)_' \
  --set-arg --epochs=1 \
  --set-arg --patience=1 \
  --set-arg --min-soft-patience=1
```

3. Solve a safe parallel plan:

```bash
python scripts/solve_schedule.py \
  --queue /path/to/queue.json \
  --profiles /path/to/resource_profiles.json \
  --cpu-limit 80 \
  --gpu-limit 80 \
  --gpu-memory-limit 90 \
  --max-workers 16
```

4. Run adaptively using the recommended `max_workers`, or a conservative value chosen by the operator:

```bash
python scripts/run_adaptive_queue.py \
  --queue /path/to/queue.json \
  --status /path/to/status.jsonl \
  --work-dir /path/to/workspace \
  --max-workers 2 \
  --cpu-limit 80 \
  --gpu-limit 80 \
  --gpu-memory-limit 90
```

## Operating Notes

- Treat `utilization.gpu` as a compute-busy throttle, not VRAM usage. Track both GPU utilization and GPU memory.
- Prefer short smoke profiles per task class before choosing parallelism.
- If profiling is unavailable, start with a conservative `max-workers` and increase only after observing stable resource use.
- Keep the queue resume-safe: every job should write a reliable marker such as `run_config.json`.
- For heterogeneous tasks, profile separate classes such as `scratch`, `foundation`, `chemprop`, and `kermt`.
- If the user needs multi-node, Kubernetes, or cloud scheduling, consider Ray, HyperQueue, Kueue, or SkyPilot instead of extending this local runner too far.

