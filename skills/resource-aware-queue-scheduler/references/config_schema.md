# Resource-Aware Queue Scheduler Schema

## Queue JSON

Required:

- `jobs`: array of job objects.
- `job_id`: unique string.
- `cmd`: command array. Prefer argv arrays over shell strings.
- `out_dir`: output directory used by the job.
- `done_file`: marker under `out_dir` used for resume/skip.

Optional job fields:

- `group`: logical task class. If missing, scripts infer it from `job_id`.
- `resource_hint`: optional static resource hints:
  - `cpu_percent`
  - `gpu_util`
  - `gpu_mem_pct`
  - `duration_sec`

Example:

```json
{
  "created_at_utc": "2026-06-22T00:00:00Z",
  "jobs": [
    {
      "job_id": "scratch_seed42",
      "group": "scratch",
      "cmd": ["python", "train.py", "--epochs", "120", "--out-dir", "/tmp/out/scratch_seed42"],
      "out_dir": "/tmp/out/scratch_seed42",
      "done_file": "run_config.json"
    }
  ]
}
```

## Resource Profiles JSON

`profile_queue.py` writes:

```json
{
  "profiles": [
    {
      "group": "scratch",
      "sample_job_id": "scratch_seed42",
      "returncode": 0,
      "duration_sec": 60.2,
      "cpu_percent_max": 320.0,
      "cpu_percent_avg": 260.0,
      "gpu_util_max": 55.0,
      "gpu_util_avg": 31.0,
      "gpu_mem_pct_max": 4.5,
      "gpu_mem_used_max": 2200.0
    }
  ]
}
```

CPU percent follows process accounting where 100 is one full CPU core. System CPU limit is sampled separately by the adaptive runner.

## Recommended Metrics

- Scheduler constraint metrics:
  - host CPU percent
  - GPU compute utilization
  - GPU memory percent
  - GPU memory used
- Throughput metrics:
  - jobs/hour
  - samples/sec
  - epoch/sec
  - total makespan

Do not use GPU memory as a proxy for compute utilization.

