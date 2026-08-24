#!/usr/bin/env python3
"""Unary-lane STREAM preflight: feasibility + Pareto over knobs.

Execute this script; do not rewrite it for a one-off audit.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
from itertools import product
from pathlib import Path
from typing import Any


def probe_hardware() -> dict[str, Any]:
    hw: dict[str, Any] = {
        "name": "probed",
        "peak_flops": None,
        "mem_gb": None,
        "vram_gb": None,
        "n_cpu": os.cpu_count() or 1,
    }
    try:
        out = subprocess.check_output(["free", "-g"], text=True)
        for line in out.splitlines():
            if line.lower().startswith("mem:"):
                hw["mem_gb"] = float(line.split()[1])
                break
    except (OSError, subprocess.CalledProcessError, ValueError, IndexError):
        pass
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        )
        row = out.strip().splitlines()[0]
        name, mem = [x.strip() for x in row.split(",", 1)]
        hw["name"] = name
        hw["vram_gb"] = round(float(mem) / 1024.0, 3)
        # Published peaks; used only as a lower-bound check.
        peaks = {"Tesla T4": 8.1e12, "NVIDIA A10": 31.2e12, "NVIDIA A100": 19.5e12}
        hw["peak_flops"] = peaks.get(name)
        hw["flops_dtype"] = "fp32_peak_lookup"
    except (OSError, subprocess.CalledProcessError, ValueError, IndexError):
        pass
    return hw


def _tile(spec: dict, B: int) -> dict[str, float]:
    table = spec["tile_s"]
    key = str(B)
    if key not in table:
        raise KeyError(f"no tile_s for B={B}; have {sorted(table)}")
    return {k: float(v) for k, v in table[key].items()}


def _partition(dyn: dict, B: int) -> tuple[int, int]:
    K = max(int(dyn["K"]), 0)
    k_hot = int(round(min(K, max(float(dyn.get("rho_hot", 1.0)), 0.0) * B)))
    rest = max(K - k_hot, 0)
    k_cold = int(round(max(min(float(dyn.get("f_expanded", 1.0)), 1.0), 0.0) * rest))
    return k_hot, k_cold


def _c_at(dyn: dict, k: int) -> float:
    return max(float(dyn["c0"]), 0.0) + max(float(dyn.get("gamma", 0.0)), 0.0) * max(k, 0)


def schedule_serial(
    A: int, t_G: float, t_M: float, t_S: float, hots: list[float], t_C: float, t_mrp: float
) -> dict[str, float | str]:
    """Next generate waits for full tile then expand (landed STREAM)."""
    t = 0.0
    t += t_C
    for k in range(A):
        t += t_G + t_M + t_S + hots[k]
    t += t_mrp
    n = A
    return {
        "T_round": t,
        "T_gpu": A * t_G,
        "T_cpu": t_C + A * t_M + sum(hots) + t_mrp,
        "T_http": A * t_S,
        "bound": "serial_sum",
    }


def schedule_three_lane(
    A: int, t_G: float, t_M: float, t_S: float, hots: list[float], t_C: float, t_mrp: float
) -> dict[str, float | str]:
    """G continuous; CPU_shared serializes C, M, H, mrp; HTTP is its own lane."""
    gpu_end = A * t_G
    cpu_free = t_C
    http_free = 0.0
    last_http = 0.0
    for k in range(A):
        g_end = (k + 1) * t_G
        m_start = max(cpu_free, g_end)
        m_end = m_start + t_M
        cpu_free = m_end + hots[k]
        s_start = max(m_end, http_free)
        last_http = s_start + t_S
        http_free = last_http
    cpu_end = cpu_free + t_mrp
    wall = max(gpu_end, cpu_end, last_http)
    if cpu_end + 1e-9 >= wall:
        bound = "cpu_shared"
    elif gpu_end + 1e-9 >= wall:
        bound = "gpu"
    else:
        bound = "http"
    return {
        "T_round": wall,
        "T_gpu": gpu_end,
        "T_cpu": cpu_end,
        "T_http": last_http,
        "bound": bound,
    }


def schedule_illegal_two(
    A: int, t_G: float, t_M: float, t_S: float, hots: list[float], t_C: float, t_mrp: float
) -> dict[str, float | str]:
    """Old fold: T_gpu = A*t_G, mat+HTTP stuffed in drain, mat∥expand."""
    t_gpu = A * t_G
    t_cpu = t_C + sum(hots) + t_mrp
    drain = t_M + t_S
    wall = max(t_gpu + drain, t_cpu)
    return {
        "T_round": wall,
        "T_gpu": t_gpu + drain,
        "T_cpu": t_cpu,
        "T_http": drain,
        "bound": "gpu" if t_gpu + drain >= t_cpu else "cpu",
    }


SCHEDULERS = {
    "serial": schedule_serial,
    "three_lane": schedule_three_lane,
    "illegal_two": schedule_illegal_two,
}


def evaluate(spec: dict, hardware: dict, fill: int, B: int, cold: str, sched: str) -> dict:
    dyn = spec["dynamics"]
    tile = _tile(spec, B)
    A = math.ceil(fill / B) if B else 0
    k_hot, k_cold = _partition(dyn, B)
    hots = [k_hot * _c_at(dyn, k) for k in range(A)]
    t_C = (k_cold * _c_at(dyn, 0)) if cold == "once" else 0.0
    if cold == "every":
        hots = [h + k_cold * _c_at(dyn, k) for k, h in enumerate(hots)]
    t_mrp = float(dyn.get("t_mrp", 0.0))
    fn = SCHEDULERS[sched]
    gantt = fn(A, tile["G"], tile["M"], tile["S"], hots, t_C, t_mrp)
    wall = float(gantt["T_round"])
    flux = fill / wall if wall > 0 else 0.0
    cap = spec.get("capacity", {})
    vram = float(cap.get("vram_base_gb", 0)) + float(cap.get("vram_per_batch_gb", 0)) * B
    mem = float(cap.get("mem_base_gb", 0)) + float(cap.get("mem_per_K_gb", 0)) * float(dyn["K"])
    flops = float(cap.get("flops_per_mol", 0)) * fill
    peak = hardware.get("peak_flops") or 0.0
    flop_s_lb = (flops / peak) if peak and flops else 0.0
    vram_cap = hardware.get("vram_gb")
    mem_cap = hardware.get("mem_gb")
    reasons = []
    if vram_cap is not None and vram > float(vram_cap):
        reasons.append(f"vram {vram:.2f}>{vram_cap}")
    if mem_cap is not None and mem > float(mem_cap):
        reasons.append(f"mem {mem:.2f}>{mem_cap}")
    if flop_s_lb and wall + 1e-9 < flop_s_lb:
        reasons.append(f"T<{flop_s_lb:.3f}s FLOP lower bound")
    landed = sched in set(spec.get("landed_schedules") or [])
    return {
        "fill": fill,
        "B": B,
        "cold": cold,
        "sched": sched,
        "A": A,
        "K_hot": k_hot,
        "K_cold": k_cold,
        "landed": landed,
        "feasible": not reasons,
        "infeasible": reasons,
        "vram_gb": round(vram, 3),
        "mem_gb": round(mem, 3),
        "flop_s_lb": round(flop_s_lb, 6),
        "flux": round(flux, 6),
        "T_round": round(wall, 4),
        "T_gpu": round(float(gantt["T_gpu"]), 4),
        "T_cpu": round(float(gantt["T_cpu"]), 4),
        "T_http": round(float(gantt["T_http"]), 4),
        "bound": gantt["bound"],
        "illegal": sched == "illegal_two",
    }


def pareto_front(rows: list[dict], *, landed_only: bool) -> list[dict]:
    cand = [
        r
        for r in rows
        if r["feasible"] and not r["illegal"] and (r["landed"] if landed_only else True)
    ]
    front = []
    for r in cand:
        dominated = False
        for o in cand:
            if o is r:
                continue
            # maximize flux, minimize T; equal on one + better on other dominates
            ge = o["flux"] >= r["flux"] - 1e-12 and o["T_round"] <= r["T_round"] + 1e-12
            gt = o["flux"] > r["flux"] + 1e-12 or o["T_round"] < r["T_round"] - 1e-12
            if ge and gt:
                dominated = True
                break
        if not dominated:
            front.append(r)
    front.sort(key=lambda x: (-x["flux"], x["T_round"]))
    return front


def solve(spec: dict, hardware: dict) -> dict:
    knobs = spec["knobs"]
    rows = []
    for fill, B, cold, sched in product(
        knobs["fill"], knobs["B"], knobs["cold"], knobs["sched"]
    ):
        rows.append(evaluate(spec, hardware, int(fill), int(B), str(cold), str(sched)))
    return {
        "schema": "pipeline_atomize_preflight.v1",
        "pipeline": spec.get("name"),
        "hardware": hardware,
        "n_evaluated": len(rows),
        "n_feasible": sum(1 for r in rows if r["feasible"]),
        "pareto_landed": pareto_front(rows, landed_only=True),
        "pareto_including_unlanded": pareto_front(rows, landed_only=False),
        "rows": rows,
        "halt_rule": (
            "Theoretically efficient iff the bound job is atomic. "
            "On capacity Pareto iff a landed feasible row is nondominated "
            "and measured T matches."
        ),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pipeline", type=Path, default=root / "examples/pipeline.retro-dual.json")
    ap.add_argument("--hardware", type=Path, default=root / "examples/hardware.t4.json")
    ap.add_argument("--probe-hardware", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    spec = json.loads(args.pipeline.read_text())
    hardware = json.loads(args.hardware.read_text())
    if args.probe_hardware:
        probed = probe_hardware()
        for k, v in probed.items():
            if v is not None:
                hardware[k] = v
        hardware["probed"] = True
    doc = solve(spec, hardware)
    text = json.dumps(doc, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    else:
        print(text)
    front = doc["pareto_landed"]
    print(
        f"# {doc['pipeline']}  feasible={doc['n_feasible']}/{doc['n_evaluated']}  "
        f"landed_pareto={len(front)}",
        flush=True,
    )
    for r in front:
        print(
            f"#   fill={r['fill']} B={r['B']} {r['cold']}/{r['sched']}  "
            f"T={r['T_round']} flux={r['flux']} bound={r['bound']}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
