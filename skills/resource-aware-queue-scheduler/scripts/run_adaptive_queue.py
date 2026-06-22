#!/usr/bin/env python3
"""Run a JSON job queue with simple CPU/GPU utilization throttling."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"time": utc_now(), **payload}, ensure_ascii=False) + "\n")


def load_jobs(queue_path: Path) -> list[dict]:
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    return queue.get("jobs", [])


def done(job: dict) -> bool:
    return (Path(job["out_dir"]) / job.get("done_file", "")).exists()


def read_cpu_times() -> tuple[int, int]:
    vals = [int(v) for v in Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
    idle = vals[3] + vals[4]
    return idle, sum(vals)


def host_cpu_percent(sample_sec: float) -> float:
    idle0, total0 = read_cpu_times()
    time.sleep(sample_sec)
    idle1, total1 = read_cpu_times()
    total_delta = max(1, total1 - total0)
    return 100.0 * (1.0 - max(0, idle1 - idle0) / total_delta)


def gpu_stats() -> dict[str, float]:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip()
    except Exception:
        return {"gpu_util": 0.0, "gpu_mem_util": 0.0, "gpu_mem_used": 0.0, "gpu_mem_total": 0.0, "gpu_mem_pct": 0.0}
    util_s, mem_util_s, used_s, total_s = [x.strip() for x in out.splitlines()[0].split(",")]
    used = float(used_s)
    total = max(1.0, float(total_s))
    return {
        "gpu_util": float(util_s),
        "gpu_mem_util": float(mem_util_s),
        "gpu_mem_used": used,
        "gpu_mem_total": total,
        "gpu_mem_pct": 100.0 * used / total,
    }


def start_job(job: dict, work_dir: Path, log_dir: Path, status: Path) -> subprocess.Popen:
    out_dir = Path(job["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{job['job_id']}.log"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(work_dir) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    append_jsonl(status, {"event": "start", "job_id": job["job_id"], "out_dir": str(out_dir), "log": str(log_path)})
    log = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(job["cmd"], cwd=str(work_dir), env=env, stdout=log, stderr=subprocess.STDOUT)
    proc._adaptive_log_handle = log  # type: ignore[attr-defined]
    return proc


def close_log(proc: subprocess.Popen) -> None:
    handle = getattr(proc, "_adaptive_log_handle", None)
    if handle is not None:
        handle.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, default=Path.cwd())
    parser.add_argument("--log-dir", type=Path, default=None)
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--cpu-limit", type=float, default=80.0)
    parser.add_argument("--gpu-limit", type=float, default=80.0)
    parser.add_argument("--gpu-memory-limit", type=float, default=90.0)
    parser.add_argument("--poll-sec", type=float, default=20.0)
    parser.add_argument("--cpu-sample-sec", type=float, default=0.5)
    args = parser.parse_args()

    log_dir = args.log_dir or (args.status.parent / "logs")
    jobs = load_jobs(args.queue)
    pending = [job for job in jobs if not done(job)]
    active: dict[str, tuple[dict, subprocess.Popen]] = {}
    failures: list[str] = []
    append_jsonl(
        args.status,
        {
            "event": "adaptive_runner_start",
            "jobs_total": len(jobs),
            "jobs_pending": len(pending),
            "max_workers": args.max_workers,
            "cpu_limit": args.cpu_limit,
            "gpu_limit": args.gpu_limit,
            "gpu_memory_limit": args.gpu_memory_limit,
        },
    )

    try:
        while pending or active:
            for job_id, (job, proc) in list(active.items()):
                rc = proc.poll()
                if rc is None:
                    continue
                close_log(proc)
                append_jsonl(args.status, {"event": "finish" if rc == 0 else "failed", "job_id": job_id, "returncode": rc})
                if rc != 0:
                    failures.append(job_id)
                del active[job_id]

            launched = 0
            while pending and len(active) < args.max_workers:
                cpu = host_cpu_percent(args.cpu_sample_sec)
                gpu = gpu_stats()
                if cpu >= args.cpu_limit or gpu["gpu_util"] >= args.gpu_limit or gpu["gpu_mem_pct"] >= args.gpu_memory_limit:
                    append_jsonl(
                        args.status,
                        {
                            "event": "throttle",
                            "active": len(active),
                            "pending": len(pending),
                            "cpu_percent": round(cpu, 2),
                            **{k: round(v, 2) for k, v in gpu.items()},
                        },
                    )
                    break
                job = pending.pop(0)
                if done(job):
                    append_jsonl(args.status, {"event": "skip_done", "job_id": job["job_id"]})
                    continue
                active[job["job_id"]] = (job, start_job(job, args.work_dir, log_dir, args.status))
                launched += 1
                time.sleep(2.0)

            if launched:
                append_jsonl(args.status, {"event": "batch_launched", "launched": launched, "active": len(active), "pending": len(pending), **gpu_stats()})
            time.sleep(args.poll_sec)
    finally:
        for job_id, (_, proc) in active.items():
            if proc.poll() is None:
                proc.terminate()
                append_jsonl(args.status, {"event": "terminated_by_runner_exit", "job_id": job_id})
            close_log(proc)

    append_jsonl(args.status, {"event": "adaptive_runner_complete", "failures": failures, "jobs_total": len(jobs)})
    if failures:
        raise SystemExit(f"failed jobs: {', '.join(failures)}")


if __name__ == "__main__":
    main()

