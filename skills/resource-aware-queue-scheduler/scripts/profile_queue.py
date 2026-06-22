#!/usr/bin/env python3
"""Smoke-profile representative jobs from a JSON queue."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path


def load_jobs(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")).get("jobs", [])


def infer_group(job: dict, group_regex: str | None) -> str:
    if job.get("group"):
        return str(job["group"])
    job_id = str(job["job_id"])
    if group_regex:
        match = re.search(group_regex, job_id)
        if match:
            return match.group(1) if match.groups() else match.group(0)
    return job_id.split("_seed")[0].split("_")[0]


def parse_set_arg(values: list[str]) -> dict[str, str]:
    overrides = {}
    for item in values:
        if "=" not in item:
            raise SystemExit(f"--set-arg must be KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        overrides[key] = value
    return overrides


def rewrite_cmd(cmd: list[str], out_dir: Path, overrides: dict[str, str]) -> list[str]:
    out = list(cmd)
    for key, value in overrides.items():
        if key in out:
            idx = out.index(key)
            if idx + 1 < len(out):
                out[idx + 1] = value
            else:
                out.append(value)
        else:
            out.extend([key, value])
    for out_key in ["--out-dir", "--output-dir", "--output"]:
        if out_key in out:
            idx = out.index(out_key)
            if idx + 1 < len(out):
                out[idx + 1] = str(out_dir)
                break
    return out


def gpu_stats() -> dict[str, float]:
    try:
        raw = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip()
    except Exception:
        return {"gpu_util": 0.0, "gpu_mem_util": 0.0, "gpu_mem_used": 0.0, "gpu_mem_total": 0.0, "gpu_mem_pct": 0.0}
    util_s, mem_util_s, used_s, total_s = [x.strip() for x in raw.splitlines()[0].split(",")]
    used = float(used_s)
    total = max(1.0, float(total_s))
    return {
        "gpu_util": float(util_s),
        "gpu_mem_util": float(mem_util_s),
        "gpu_mem_used": used,
        "gpu_mem_total": total,
        "gpu_mem_pct": 100.0 * used / total,
    }


def proc_cpu(pid: int) -> float:
    try:
        out = subprocess.check_output(["ps", "-p", str(pid), "-o", "%cpu="], text=True).strip()
        return float(out or 0.0)
    except Exception:
        return 0.0


def profile_one(job: dict, group: str, cmd: list[str], work_dir: Path, profile_root: Path, sample_sec: float, timeout_sec: float) -> dict:
    out_dir = profile_root / group / job["job_id"]
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "profile.log"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(work_dir) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    start = time.time()
    samples = []
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, cwd=str(work_dir), env=env, stdout=log, stderr=subprocess.STDOUT)
        while proc.poll() is None:
            gpu = gpu_stats()
            samples.append({"t": time.time() - start, "cpu_percent": proc_cpu(proc.pid), **gpu})
            if timeout_sec > 0 and time.time() - start > timeout_sec:
                proc.terminate()
                time.sleep(5)
                if proc.poll() is None:
                    proc.kill()
                break
            time.sleep(sample_sec)
        returncode = proc.poll()
    duration = time.time() - start
    if not samples:
        samples.append({"cpu_percent": 0.0, **gpu_stats()})
    return {
        "group": group,
        "sample_job_id": job["job_id"],
        "returncode": returncode,
        "duration_sec": round(duration, 3),
        "log": str(log_path),
        "cpu_percent_max": max(s["cpu_percent"] for s in samples),
        "cpu_percent_avg": sum(s["cpu_percent"] for s in samples) / len(samples),
        "gpu_util_max": max(s["gpu_util"] for s in samples),
        "gpu_util_avg": sum(s["gpu_util"] for s in samples) / len(samples),
        "gpu_mem_pct_max": max(s["gpu_mem_pct"] for s in samples),
        "gpu_mem_used_max": max(s["gpu_mem_used"] for s in samples),
        "gpu_mem_total": max(s["gpu_mem_total"] for s in samples),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--profile-out", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, default=Path.cwd())
    parser.add_argument("--profile-root", type=Path, required=True)
    parser.add_argument("--group-regex", default=None)
    parser.add_argument("--set-arg", action="append", default=[])
    parser.add_argument("--sample-sec", type=float, default=2.0)
    parser.add_argument("--timeout-sec", type=float, default=0.0)
    args = parser.parse_args()

    overrides = parse_set_arg(args.set_arg)
    jobs = load_jobs(args.queue)
    representatives: dict[str, dict] = {}
    for job in jobs:
        group = infer_group(job, args.group_regex)
        representatives.setdefault(group, job)

    profiles = []
    for group, job in representatives.items():
        profile_out_dir = args.profile_root / group / job["job_id"]
        cmd = rewrite_cmd(job["cmd"], profile_out_dir, overrides)
        profiles.append(profile_one(job, group, cmd, args.work_dir, args.profile_root, args.sample_sec, args.timeout_sec))

    args.profile_out.parent.mkdir(parents=True, exist_ok=True)
    args.profile_out.write_text(json.dumps({"profiles": profiles}, indent=2), encoding="utf-8")
    print(json.dumps({"profile_out": str(args.profile_out), "groups": len(profiles), "profiles": profiles}, indent=2))


if __name__ == "__main__":
    main()

