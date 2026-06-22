#!/usr/bin/env python3
"""Estimate a simple resource-constrained parallel schedule from smoke profiles."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path


def infer_group(job: dict, group_regex: str | None) -> str:
    if job.get("group"):
        return str(job["group"])
    job_id = str(job["job_id"])
    if group_regex:
        match = re.search(group_regex, job_id)
        if match:
            return match.group(1) if match.groups() else match.group(0)
    return job_id.split("_seed")[0].split("_")[0]


def load_profiles(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {p["group"]: p for p in data.get("profiles", [])}


def simulate(tasks: list[dict], cpu_limit: float, gpu_limit: float, gpu_memory_limit: float, max_workers: int) -> dict:
    now = 0.0
    pending = sorted(tasks, key=lambda t: t["duration_sec"], reverse=True)
    active: list[dict] = []
    peak = {"cpu_percent": 0.0, "gpu_util": 0.0, "gpu_mem_pct": 0.0, "workers": 0}
    while pending or active:
        started = True
        while pending and len(active) < max_workers and started:
            started = False
            current = {
                "cpu_percent": sum(t["cpu_percent"] for t in active),
                "gpu_util": sum(t["gpu_util"] for t in active),
                "gpu_mem_pct": sum(t["gpu_mem_pct"] for t in active),
            }
            for idx, task in enumerate(pending):
                nxt = {
                    "cpu_percent": current["cpu_percent"] + task["cpu_percent"],
                    "gpu_util": current["gpu_util"] + task["gpu_util"],
                    "gpu_mem_pct": current["gpu_mem_pct"] + task["gpu_mem_pct"],
                }
                if nxt["cpu_percent"] <= cpu_limit and nxt["gpu_util"] <= gpu_limit and nxt["gpu_mem_pct"] <= gpu_memory_limit:
                    task = pending.pop(idx)
                    task = {**task, "end": now + task["duration_sec"]}
                    active.append(task)
                    peak["cpu_percent"] = max(peak["cpu_percent"], nxt["cpu_percent"])
                    peak["gpu_util"] = max(peak["gpu_util"], nxt["gpu_util"])
                    peak["gpu_mem_pct"] = max(peak["gpu_mem_pct"], nxt["gpu_mem_pct"])
                    peak["workers"] = max(peak["workers"], len(active))
                    started = True
                    break
        if active:
            now = min(t["end"] for t in active)
            active = [t for t in active if t["end"] > now + 1.0e-9]
        elif pending:
            task = pending.pop(0)
            task = {**task, "end": now + task["duration_sec"]}
            active.append(task)
            peak["workers"] = max(peak["workers"], 1)
    return {"makespan_sec": now, "peak": peak}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--profiles", type=Path, required=True)
    parser.add_argument("--group-regex", default=None)
    parser.add_argument("--cpu-limit", type=float, default=80.0, help="Host CPU percentage, 0-100")
    parser.add_argument("--gpu-limit", type=float, default=80.0)
    parser.add_argument("--gpu-memory-limit", type=float, default=90.0)
    parser.add_argument("--max-workers", type=int, default=16)
    args = parser.parse_args()

    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    profiles = load_profiles(args.profiles)
    tasks = []
    missing = []
    counts = Counter()
    for job in queue.get("jobs", []):
        group = infer_group(job, args.group_regex)
        counts[group] += 1
        profile = profiles.get(group)
        if not profile:
            missing.append(group)
            continue
        tasks.append(
            {
                "job_id": job["job_id"],
                "group": group,
                "duration_sec": max(1.0, float(profile["duration_sec"])),
                "cpu_percent": min(100.0, float(profile.get("cpu_percent_avg", profile.get("cpu_percent_max", 0.0))) / max(1, os_cpu_count())),
                "gpu_util": float(profile.get("gpu_util_avg", profile.get("gpu_util_max", 0.0))),
                "gpu_mem_pct": float(profile.get("gpu_mem_pct_max", 0.0)),
            }
        )
    if missing:
        missing = sorted(set(missing))
    trials = []
    for workers in range(1, args.max_workers + 1):
        trials.append({"max_workers": workers, **simulate(tasks, args.cpu_limit, args.gpu_limit, args.gpu_memory_limit, workers)})
    best = min(trials, key=lambda t: t["makespan_sec"]) if trials else None
    print(
        json.dumps(
            {
                "job_counts_by_group": dict(counts),
                "missing_profile_groups": missing,
                "recommended": best,
                "trials": trials,
                "notes": [
                    "Smoke profiles are approximations; validate with live adaptive throttling.",
                    "CPU profile is normalized to host-level percent for schedule simulation.",
                    "GPU utilization is compute-busy percentage, not VRAM usage.",
                ],
            },
            indent=2,
        )
    )


def os_cpu_count() -> int:
    try:
        return len(__import__("os").sched_getaffinity(0))
    except Exception:
        return __import__("os").cpu_count() or 1


if __name__ == "__main__":
    main()

