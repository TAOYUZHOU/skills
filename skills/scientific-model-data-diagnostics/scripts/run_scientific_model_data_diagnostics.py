#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def finite_pair(y: pd.Series, pred: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    yv = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float)
    pv = pd.to_numeric(pred, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(yv) & np.isfinite(pv)
    return yv[mask], pv[mask]


def regression_metrics(y: pd.Series, pred: pd.Series) -> dict[str, float | int | str]:
    yv, pv = finite_pair(y, pred)
    n = int(len(yv))
    if n == 0:
        return {
            "n": 0,
            "r2": np.nan,
            "mae": np.nan,
            "rmse": np.nan,
            "bias_pred_minus_obs": np.nan,
            "target_mean": np.nan,
            "target_std": np.nan,
            "pred_mean": np.nan,
            "metric_reliability": "no_labeled_rows",
        }
    residual = pv - yv
    denom = float(((yv - yv.mean()) ** 2).sum())
    r2 = np.nan if n < 2 or denom == 0 else 1.0 - float(((yv - pv) ** 2).sum()) / denom
    target_std = float(np.std(yv, ddof=0))
    reliability = "ok"
    if n < 20:
        reliability = "fragile_small_n"
    if target_std < 0.5:
        reliability = "fragile_narrow_label_range" if reliability == "ok" else reliability + "+narrow_label_range"
    return {
        "n": n,
        "r2": r2,
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "bias_pred_minus_obs": float(np.mean(residual)),
        "target_mean": float(np.mean(yv)),
        "target_std": target_std,
        "pred_mean": float(np.mean(pv)),
        "metric_reliability": reliability,
    }


def classification_metrics(y: pd.Series, prob: pd.Series) -> dict[str, float | int | str]:
    yv = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float)
    pv = pd.to_numeric(prob, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(yv) & np.isfinite(pv)
    yb = yv[mask].astype(int)
    pb = (pv[mask] >= 0.5).astype(int)
    n = int(len(yb))
    if n == 0:
        return {
            "n": 0,
            "positive": 0,
            "positive_rate": np.nan,
            "accuracy": np.nan,
            "f1": np.nan,
            "tp": 0,
            "fp": 0,
            "tn": 0,
            "fn": 0,
            "metric_reliability": "no_labeled_rows",
        }
    tp = int(((pb == 1) & (yb == 1)).sum())
    fp = int(((pb == 1) & (yb == 0)).sum())
    tn = int(((pb == 0) & (yb == 0)).sum())
    fn = int(((pb == 0) & (yb == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    positives = int(yb.sum())
    reliability = "ok"
    if positives == 0 or positives == n:
        reliability = "not_interpretable_single_class"
    elif positives < 5 or (n - positives) < 5:
        reliability = "fragile_rare_class"
    return {
        "n": n,
        "positive": positives,
        "positive_rate": float(yb.mean()),
        "accuracy": float((pb == yb).mean()),
        "f1": float(f1),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "metric_reliability": reliability,
    }


def normalize_group_value(value: object) -> str:
    if pd.isna(value):
        return "MISSING"
    text = str(value)
    return text if len(text) <= 160 else text[:157] + "..."


def group_diagnostics(
    df: pd.DataFrame,
    group_cols: Iterable[str],
    target_col: str,
    pred_col: str,
    min_group_n: int,
) -> pd.DataFrame:
    rows = []
    rows.append({"group_col": "__all__", "group_value": "all", **regression_metrics(df[target_col], df[pred_col])})
    for col in group_cols:
        if col not in df.columns:
            continue
        for value, group in df.groupby(col, dropna=False, observed=False):
            metrics = regression_metrics(group[target_col], group[pred_col])
            if metrics["n"] < min_group_n:
                continue
            rows.append({"group_col": col, "group_value": normalize_group_value(value), **metrics})
    return pd.DataFrame(rows)


def class_group_diagnostics(
    df: pd.DataFrame,
    group_cols: Iterable[str],
    target_col: str,
    prob_col: str,
    min_group_n: int,
) -> pd.DataFrame:
    rows = []
    rows.append({"group_col": "__all__", "group_value": "all", **classification_metrics(df[target_col], df[prob_col])})
    for col in group_cols:
        if col not in df.columns:
            continue
        for value, group in df.groupby(col, dropna=False, observed=False):
            metrics = classification_metrics(group[target_col], group[prob_col])
            if metrics["n"] < min_group_n:
                continue
            rows.append({"group_col": col, "group_value": normalize_group_value(value), **metrics})
    return pd.DataFrame(rows)


def maybe_apply_mask(df: pd.DataFrame, mask_col: str | None) -> pd.DataFrame:
    if not mask_col or mask_col not in df.columns:
        return df.copy()
    mask = pd.to_numeric(df[mask_col], errors="coerce").fillna(0) > 0
    return df[mask].copy()


def apply_filters(df: pd.DataFrame, filters: list[str]) -> pd.DataFrame:
    out = df
    for item in filters:
        if "=" not in item:
            raise SystemExit(f"filter must use col=value syntax: {item}")
        col, value = item.split("=", 1)
        if col not in out.columns:
            raise SystemExit(f"filter column not found: {col}")
        if value == "MISSING":
            out = out[out[col].isna()]
        else:
            out = out[out[col].astype(str) == value]
    return out.copy()


def write_figures(out_dir: Path, reg: pd.DataFrame, residuals: pd.DataFrame, target_col: str, pred_col: str) -> list[str]:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return []
    figure_dir = out_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    ranked = reg[reg["group_col"].ne("__all__")].sort_values("r2", ascending=True).head(20)
    if not ranked.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        labels = ranked["group_col"].astype(str) + "=" + ranked["group_value"].astype(str)
        ax.barh(np.arange(len(ranked)), ranked["r2"].to_numpy(dtype=float), color="#4C78A8")
        ax.axvline(0, color="black", linewidth=0.9)
        ax.set_yticks(np.arange(len(ranked)))
        ax.set_yticklabels(labels)
        ax.set_xlabel("R2")
        ax.set_title("Worst subgroup R2 diagnostics")
        fig.tight_layout()
        path = figure_dir / "worst_subgroup_r2.png"
        fig.savefig(path, dpi=180)
        plt.close(fig)
        written.append(str(path))

    if not residuals.empty:
        fig, ax = plt.subplots(figsize=(5.5, 5.5))
        ax.scatter(residuals[target_col], residuals[pred_col], s=14, alpha=0.7)
        mn = float(np.nanmin([residuals[target_col].min(), residuals[pred_col].min()]))
        mx = float(np.nanmax([residuals[target_col].max(), residuals[pred_col].max()]))
        ax.plot([mn, mx], [mn, mx], color="black", linewidth=1)
        ax.set_xlabel("Observed")
        ax.set_ylabel("Predicted")
        ax.set_title("Observed vs predicted")
        fig.tight_layout()
        path = figure_dir / "observed_vs_predicted.png"
        fig.savefig(path, dpi=180)
        plt.close(fig)
        written.append(str(path))
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ML data diagnostics from predictions and metadata CSVs.")
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--join-key", default="sample_idx")
    parser.add_argument("--target-col", required=True)
    parser.add_argument("--pred-col", required=True)
    parser.add_argument("--mask-col")
    parser.add_argument("--group-cols", nargs="*", default=[])
    parser.add_argument("--class-target-col")
    parser.add_argument("--class-prob-col")
    parser.add_argument("--class-mask-col")
    parser.add_argument("--filter", action="append", default=[], help="Restrict rows before diagnostics, using col=value. Use MISSING for nulls. Repeatable.")
    parser.add_argument("--min-group-n", type=int, default=8)
    parser.add_argument("--top-residuals", type=int, default=50)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    pred = pd.read_csv(args.predictions)
    if args.metadata:
        meta = pd.read_csv(args.metadata)
        if args.join_key not in pred.columns or args.join_key not in meta.columns:
            raise SystemExit(f"join key {args.join_key!r} must exist in both predictions and metadata")
        meta_cols = [c for c in meta.columns if c == args.join_key or c not in pred.columns]
        df = pred.merge(meta[meta_cols], on=args.join_key, how="left")
    else:
        df = pred

    for col in [args.target_col, args.pred_col]:
        if col not in df.columns:
            raise SystemExit(f"missing required column: {col}")

    df = apply_filters(df, args.filter)
    reg_df = maybe_apply_mask(df, args.mask_col)
    reg = group_diagnostics(reg_df, args.group_cols, args.target_col, args.pred_col, args.min_group_n)
    reg.to_csv(args.out_dir / "regression_group_diagnostics.csv", index=False)

    residual_df = reg_df.copy()
    residual_df["residual_pred_minus_obs"] = pd.to_numeric(residual_df[args.pred_col], errors="coerce") - pd.to_numeric(
        residual_df[args.target_col], errors="coerce"
    )
    residual_df["abs_residual"] = residual_df["residual_pred_minus_obs"].abs()
    keep_cols = [
        args.join_key,
        args.target_col,
        args.pred_col,
        "residual_pred_minus_obs",
        "abs_residual",
        *[c for c in args.group_cols if c in residual_df.columns],
    ]
    residual_df.sort_values("abs_residual", ascending=False)[keep_cols].head(args.top_residuals).to_csv(
        args.out_dir / "top_residuals.csv", index=False
    )

    class_path = None
    if args.class_target_col and args.class_prob_col:
        if args.class_target_col not in df.columns or args.class_prob_col not in df.columns:
            raise SystemExit("classification target/probability columns must exist when provided")
        class_df = maybe_apply_mask(df, args.class_mask_col)
        class_diag = class_group_diagnostics(
            class_df, args.group_cols, args.class_target_col, args.class_prob_col, args.min_group_n
        )
        class_path = args.out_dir / "classification_group_diagnostics.csv"
        class_diag.to_csv(class_path, index=False)

    figures = write_figures(args.out_dir, reg, residual_df, args.target_col, args.pred_col)
    summary = {
        "predictions": str(args.predictions),
        "metadata": str(args.metadata) if args.metadata else None,
        "filters": args.filter,
        "rows_joined": int(len(df)),
        "regression_rows_after_mask": int(len(reg_df)),
        "regression_group_diagnostics": str(args.out_dir / "regression_group_diagnostics.csv"),
        "classification_group_diagnostics": str(class_path) if class_path else None,
        "top_residuals": str(args.out_dir / "top_residuals.csv"),
        "figures": figures,
    }
    (args.out_dir / "diagnostic_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(args.out_dir)


if __name__ == "__main__":
    main()
