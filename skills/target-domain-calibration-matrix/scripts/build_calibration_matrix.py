#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any

import pandas as pd


ID_CANDIDATES = [
    "canonical_smiles",
    "smiles",
    "molecule_id",
    "mol_id",
    "compound_id",
    "inchi_key",
    "inchikey",
]
SCAFFOLD_CANDIDATES = ["scaffold", "murcko_scaffold", "bemis_murcko_scaffold"]
SIM_CANDIDATES = ["max_tanimoto_to_train", "max_tanimoto", "train_max_tanimoto"]
TEMPLATE_CANDIDATES = ["template_family", "dominant_template_family", "template_name", "template_id", "matched_templates"]
SOURCE_CANDIDATES = ["source_id", "supervision_source", "source", "protocol"]


def pick_column(df: pd.DataFrame, requested: str | None, candidates: list[str], fallback: str | None = None) -> str:
    if requested:
        if requested not in df.columns:
            raise SystemExit(f"Requested column not found: {requested}")
        return requested
    for col in candidates:
        if col in df.columns:
            return col
    if fallback:
        return fallback
    raise SystemExit(f"Could not infer a column from candidates: {candidates}")


def normalize_frac(value: str) -> tuple[str, float | None, int | None]:
    text = str(value).strip()
    if text.lower().startswith("k="):
        k = int(text.split("=", 1)[1])
        return f"k{k}", None, k
    x = float(text)
    label = f"p{str(x).replace('.', 'p')}"
    return label, x, None


def group_table(df: pd.DataFrame, group_col: str, id_col: str, strategy_cols: dict[str, str | None]) -> pd.DataFrame:
    rows = []
    for group, part in df.groupby(group_col, dropna=False):
        row: dict[str, Any] = {
            "group_id": str(group),
            "rows": int(len(part)),
            "molecules": int(part[id_col].nunique()),
        }
        for key, col in strategy_cols.items():
            if col and col in part.columns:
                if key == "similarity":
                    row[key] = pd.to_numeric(part[col], errors="coerce").median()
                else:
                    mode = part[col].dropna().astype(str).mode()
                    row[key] = mode.iloc[0] if len(mode) else "NA"
            else:
                row[key] = "NA"
        rows.append(row)
    return pd.DataFrame(rows)


def choose_holdout(groups: pd.DataFrame, holdout_frac: float, seed: int) -> set[str]:
    shuffled = groups.sample(frac=1, random_state=seed).reset_index(drop=True)
    target_rows = max(1, int(round(groups["rows"].sum() * holdout_frac)))
    chosen: list[str] = []
    total = 0
    for _, row in shuffled.iterrows():
        if total >= target_rows and chosen:
            break
        chosen.append(str(row["group_id"]))
        total += int(row["rows"])
    return set(chosen)


def sample_groups(pool: pd.DataFrame, label: str, frac: float | None, k: int | None, strategy: str, seed: int) -> set[str]:
    if frac == 0 or k == 0:
        return set()
    if k is None:
        k = max(1, int(math.ceil(len(pool) * float(frac))))
    k = min(k, len(pool))
    if k <= 0:
        return set()
    rng = random.Random(seed)
    if strategy == "random":
        group_ids = pool["group_id"].astype(str).tolist()
        rng.shuffle(group_ids)
        return set(group_ids[:k])
    if strategy == "scaffold_diverse":
        # Groups already represent scaffolds when scaffold metadata exists; row-count ascending avoids over-sampling large families first.
        ordered = pool.sort_values(["rows", "group_id"], ascending=[True, True])
        return set(ordered["group_id"].astype(str).head(k))
    if strategy == "low_similarity_frontier" and "similarity" in pool.columns:
        tmp = pool.copy()
        tmp["_similarity"] = pd.to_numeric(tmp["similarity"], errors="coerce").fillna(1.0)
        return set(tmp.sort_values(["_similarity", "group_id"], ascending=[True, True])["group_id"].astype(str).head(k))
    if strategy in {"template_family_balanced", "source_protocol_balanced"}:
        col = "template" if strategy == "template_family_balanced" else "source"
        if col in pool.columns:
            selected: list[str] = []
            buckets = [g for _, g in pool.sort_values("group_id").groupby(col, dropna=False)]
            while len(selected) < k and buckets:
                next_buckets = []
                for bucket in buckets:
                    if len(selected) >= k:
                        break
                    if len(bucket):
                        selected.append(str(bucket.iloc[0]["group_id"]))
                        rest = bucket.iloc[1:]
                        if len(rest):
                            next_buckets.append(rest)
                buckets = next_buckets
            return set(selected[:k])
    return sample_groups(pool, label, frac, k, "random", seed)


def render_command(template: dict[str, Any], values: dict[str, str]) -> list[str]:
    return [str(part).format(**values) for part in template.get("cmd", [])]


def load_architectures(path: Path | None) -> list[dict[str, Any]]:
    if not path:
        return [{"name": "default", "family": "unknown", "command_args": {}}]
    data = json.loads(path.read_text(encoding="utf-8"))
    archs = data.get("architectures", data if isinstance(data, list) else [])
    if not archs:
        raise SystemExit(f"No architectures found in {path}")
    return archs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build target-domain calibration matrix splits and queue JSON.")
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--domain-col", default="abc_set")
    parser.add_argument("--split-col", default="split")
    parser.add_argument("--train-split-values", nargs="+", default=["train"])
    parser.add_argument("--target-domain", default="C")
    parser.add_argument("--source-domains", nargs="+", default=["A", "B"])
    parser.add_argument("--id-col")
    parser.add_argument("--scaffold-col")
    parser.add_argument("--similarity-col")
    parser.add_argument("--template-col")
    parser.add_argument("--source-col")
    parser.add_argument("--holdout-frac", type=float, default=0.5)
    parser.add_argument("--holdout-seed", type=int, default=20260623)
    parser.add_argument("--calibration-fracs", nargs="+", default=["0", "0.005", "0.01", "0.025", "0.05", "0.10", "0.20"])
    parser.add_argument("--strategies", nargs="+", default=["random", "scaffold_diverse", "low_similarity_frontier"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--architecture-config", type=Path)
    parser.add_argument("--command-template", type=Path)
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()

    df = pd.read_csv(args.metadata)
    if args.domain_col not in df.columns:
        raise SystemExit(f"Domain column not found: {args.domain_col}")
    id_col = pick_column(df, args.id_col, ID_CANDIDATES)
    scaffold_col = pick_column(df, args.scaffold_col, SCAFFOLD_CANDIDATES, fallback=id_col)
    similarity_col = pick_column(df, args.similarity_col, SIM_CANDIDATES, fallback=None) if any(c in df.columns for c in SIM_CANDIDATES) or args.similarity_col else None
    template_col = pick_column(df, args.template_col, TEMPLATE_CANDIDATES, fallback=None) if any(c in df.columns for c in TEMPLATE_CANDIDATES) or args.template_col else None
    source_col = pick_column(df, args.source_col, SOURCE_CANDIDATES, fallback=None) if any(c in df.columns for c in SOURCE_CANDIDATES) or args.source_col else None

    out = args.out_dir
    splits_dir = out / "splits"
    out.mkdir(parents=True, exist_ok=True)
    splits_dir.mkdir(parents=True, exist_ok=True)

    target = df[df[args.domain_col].astype(str) == str(args.target_domain)].copy()
    if target.empty:
        raise SystemExit(f"No target-domain rows found for {args.target_domain}")
    source_domain_mask = df[args.domain_col].astype(str).isin([str(x) for x in args.source_domains])
    if args.split_col in df.columns:
        source_train_mask = source_domain_mask & df[args.split_col].astype(str).isin([str(x) for x in args.train_split_values])
        source_eval_mask = source_domain_mask & ~df[args.split_col].astype(str).isin([str(x) for x in args.train_split_values])
    else:
        source_train_mask = source_domain_mask
        source_eval_mask = pd.Series(False, index=df.index)

    strategy_cols = {"similarity": similarity_col, "template": template_col, "source": source_col}
    groups = group_table(target, scaffold_col, id_col, strategy_cols)
    holdout_groups = choose_holdout(groups, args.holdout_frac, args.holdout_seed)
    pool_groups = groups[~groups["group_id"].astype(str).isin(holdout_groups)].copy()
    holdout_group_path = out / "target_holdout_groups.csv"
    groups.assign(role=groups["group_id"].astype(str).map(lambda x: "target_heldout_test" if x in holdout_groups else "target_calibration_pool")).to_csv(holdout_group_path, index=False)

    archs = load_architectures(args.architecture_config)
    template = json.loads(args.command_template.read_text(encoding="utf-8")) if args.command_template else None
    jobs: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []

    for arch in archs:
        arch_name = str(arch.get("name", "default"))
        for strategy in args.strategies:
            for frac_text in args.calibration_fracs:
                frac_label, frac, k = normalize_frac(frac_text)
                for seed in args.seeds:
                    selected = sample_groups(pool_groups, frac_label, frac, k, strategy, seed)
                    job_id = f"{arch_name}_{strategy}_{frac_label}_seed{seed}"
                    split = df.copy()
                    split["calibration_role"] = "unused"
                    split.loc[source_train_mask, "calibration_role"] = "source_train"
                    split.loc[source_eval_mask, "calibration_role"] = "source_eval"
                    target_group = split[scaffold_col].astype(str)
                    split.loc[(split[args.domain_col].astype(str) == str(args.target_domain)) & target_group.isin(holdout_groups), "calibration_role"] = "target_heldout_test"
                    split.loc[(split[args.domain_col].astype(str) == str(args.target_domain)) & target_group.isin(selected), "calibration_role"] = "target_calibration_train"
                    split.loc[(split[args.domain_col].astype(str) == str(args.target_domain)) & ~(target_group.isin(holdout_groups | selected)), "calibration_role"] = "target_calibration_unused"
                    split["calibration_strategy"] = strategy
                    split["calibration_fraction"] = frac_text
                    split["calibration_seed"] = seed
                    split["architecture"] = arch_name
                    split_path = splits_dir / f"{job_id}.csv"
                    split.to_csv(split_path, index=False)

                    selected_rows = int((split["calibration_role"] == "target_calibration_train").sum())
                    heldout_rows = int((split["calibration_role"] == "target_heldout_test").sum())
                    manifest_rows.append({
                        "job_id": job_id,
                        "architecture": arch_name,
                        "strategy": strategy,
                        "calibration_size": frac_text,
                        "seed": seed,
                        "split_csv": str(split_path),
                        "selected_target_groups": len(selected),
                        "selected_target_rows": selected_rows,
                        "target_heldout_rows": heldout_rows,
                    })
                    if template:
                        job_out = out / "runs" / job_id
                        values = {
                            "job_id": job_id,
                            "architecture": arch_name,
                            "strategy": strategy,
                            "calibration_frac": frac_text,
                            "target_domain": str(args.target_domain),
                            "seed": str(seed),
                            "split_csv": str(split_path),
                            "out_dir": str(job_out),
                        }
                        jobs.append({
                            "job_id": job_id,
                            "cmd": render_command(template, values),
                            "out_dir": str(job_out),
                            "done_file": template.get("done_file", "run_config.json"),
                        })

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = out / "calibration_matrix_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    queue_path = out / "calibration_queue.json"
    if template:
        queue_path.write_text(json.dumps({"jobs": jobs}, indent=2), encoding="utf-8")

    lock = out / "CALIBRATION_MATRIX_LOCK.md"
    lock.write_text(
        "\n".join([
            "# Target-Domain Calibration Matrix Lock",
            "",
            f"- Metadata: `{args.metadata}`",
            f"- Domain column: `{args.domain_col}`",
            f"- Split column: `{args.split_col if args.split_col in df.columns else 'not found; all source-domain rows treated as train'}`",
            f"- Train split values: `{', '.join(args.train_split_values)}`",
            f"- Source domains: `{', '.join(args.source_domains)}`",
            f"- Target domain: `{args.target_domain}`",
            f"- Group column: `{scaffold_col}`",
            f"- Holdout fraction: `{args.holdout_frac}`",
            f"- Holdout seed: `{args.holdout_seed}`",
            f"- Target groups: `{len(groups)}`",
            f"- Target calibration-pool groups: `{len(pool_groups)}`",
            f"- Target heldout groups: `{len(holdout_groups)}`",
            f"- Matrix rows: `{len(manifest)}`",
            f"- Manifest: `{manifest_path}`",
            f"- Queue: `{queue_path if template else 'not generated; no command template provided'}`",
            "",
            "Target held-out rows must not be used for training, model selection, residual-driven sampling, or queue retries that change the calibration split.",
        ]) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "manifest": str(manifest_path),
        "queue": str(queue_path) if template else None,
        "lock": str(lock),
        "splits": len(manifest),
        "target_holdout_groups": str(holdout_group_path),
    }, indent=2))


if __name__ == "__main__":
    main()
