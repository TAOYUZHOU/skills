#!/usr/bin/env python3
"""Attach Dual fill-budget / n_iter to a preflight.v1 document.

Does not rewrite preflight_solver.py. The solver still reports one fill-round.
This composes the missing tree layer:

    n_work <= mssr * fill
    n_iter = min(mssr, drain_rounds)
    T_tree = n_iter * T_round   (only when n_iter is measured)

Usage:
  python compose_search_volume.py \\
    --preflight preflight.ts_bound.json \\
    --volume search_volume.json \\
    --out preflight.tree.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def attach(preflight: dict, volume: dict) -> dict:
    mssr = int(volume["mssr"])
    measured = volume.get("n_iter_measured") or {}
    live = volume.get("live_tree") or {}
    rows = []
    for r in preflight["rows"]:
        fill = int(r["fill"])
        B = int(r["B"])
        key = f"{fill}"
        n_iter = None
        src = None
        by_b = measured.get(key) or measured.get(str(fill)) or {}
        if str(B) in by_b:
            n_iter = int(by_b[str(B)])
            src = "measured"
        n_work_cap = mssr * fill
        t_round = float(r["T_round"])
        out = dict(r)
        out["mssr"] = mssr
        out["n_work_cap"] = n_work_cap
        out["T_tree_cap"] = round(mssr * t_round, 4)
        out["n_iter"] = n_iter
        out["n_iter_source"] = src
        out["n_work_hat"] = (n_iter * fill) if n_iter is not None else None
        out["T_tree_hat"] = (
            round(n_iter * t_round, 4) if n_iter is not None else None
        )
        live_key = f"{fill}:{B}"
        if live_key in live:
            L = live[live_key]
            out["T_tree_live"] = L.get("wall_s")
            out["n_work_live"] = L.get("step_mols")
            out["n_iter_live"] = L.get("n_iter")
            if out["T_tree_hat"] and L.get("wall_s"):
                pred = out["T_tree_hat"]
                meas = float(L["wall_s"])
                out["T_tree_err_pct"] = round(100.0 * (pred - meas) / meas, 1)
        rows.append(out)

    def tree_front(cand):
        usable = [
            x
            for x in cand
            if x.get("landed")
            and x.get("feasible")
            and x.get("T_tree_hat") is not None
        ]
        keep = []
        for r in usable:
            dominated = False
            for o in usable:
                if o is r:
                    continue
                ge = o["n_work_hat"] >= r["n_work_hat"] and o["T_tree_hat"] <= r[
                    "T_tree_hat"
                ]
                gt = o["n_work_hat"] > r["n_work_hat"] or o["T_tree_hat"] < r[
                    "T_tree_hat"
                ]
                if ge and gt:
                    dominated = True
                    break
            if not dominated:
                keep.append(r)
        keep.sort(key=lambda x: (x["T_tree_hat"], -x["n_work_hat"]))
        return keep

    doc = dict(preflight)
    doc["schema"] = "pipeline_atomize_preflight.tree.v1"
    doc["volume"] = {
        "mssr": mssr,
        "note": volume.get("note"),
        "n_iter_measured": measured,
    }
    doc["rows"] = rows
    doc["pareto_tree_landed"] = tree_front(rows)
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preflight", type=Path, required=True)
    ap.add_argument("--volume", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    doc = attach(
        json.loads(args.preflight.read_text()),
        json.loads(args.volume.read_text()),
    )
    args.out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(
        f"# tree compose  rows={len(doc['rows'])}  "
        f"tree_front={len(doc['pareto_tree_landed'])}",
        flush=True,
    )
    for r in doc["pareto_tree_landed"]:
        print(
            f"#   fill={r['fill']} B={r['B']} n_iter={r['n_iter']} "
            f"T_round={r['T_round']} T_tree_hat={r['T_tree_hat']} "
            f"err={r.get('T_tree_err_pct')}%",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
