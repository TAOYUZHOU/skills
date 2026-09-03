#!/usr/bin/env python3
"""Convert moltrek/patent route JSON into gold compact-L-tree data.js and write a site.

All imports stay inside this skill directory, plus optional installed packages
(rdkit, c12_search). No host or sibling-repo paths.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional

SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS = SKILL_DIR / "assets"
sys.path[:0] = [str(SKILL_DIR / "scripts")]

from rdkit_svg import smiles_to_svg  # noqa: E402
from route_parse import get_reaction_from_smiles  # noqa: E402
from v4_local import (  # noqa: E402
    is_search_inorganic,
    route_logS_from_steps,
    try_bbl_buyable_fn,
    try_membership_batch,
    try_path_local_str_audits,
)


def walk(node: dict) -> Iterable[dict]:
    yield node
    for ch in node.get("Children") or node.get("children") or []:
        if isinstance(ch, dict):
            yield from walk(ch)


def rxn_of(node: dict) -> str:
    return (
        node.get("Formula")
        or node.get("rxn")
        or node.get("OriFormula")
        or node.get("rxn0")
        or ""
    ).strip()


def target_of(node: dict) -> str:
    tgt = node.get("TargetMol") or node.get("target") or ""
    if tgt:
        return tgt
    rxn = rxn_of(node)
    if ">>" in rxn:
        return rxn.split(">>", 1)[1].strip()
    return ""


def children_of(node: dict) -> List[dict]:
    return [c for c in (node.get("Children") or node.get("children") or []) if isinstance(c, dict)]


def reactants_of(node: dict) -> List[str]:
    # OriFormula is the aromatic/search form; Formula is often Kekulé.
    # Prefer Ori so leftover SMILES match bbl_leaves and child canons.
    rxn = (node.get("OriFormula") or rxn_of(node) or "").strip()
    main = node.get("main_material") or ""
    if ">>" not in rxn:
        return []
    reactants, _ = get_reaction_from_smiles(rxn, main or None)
    return [r for r in reactants if r]


def existence_of(smi: str, memb: Dict[str, Any]) -> str:
    info = memb.get(smi)
    if isinstance(info, str):
        return info if info in {"reaction-dataset", "pubchem", "none"} else "none"
    info = info or {}
    if info.get("in_reaction_dataset"):
        return "reaction-dataset"
    if info.get("in_pubchem"):
        return "pubchem"
    return "none"


def terminal_class(smi: str, memb: Dict[str, Any]) -> str:
    existence = existence_of(smi, memb)
    if existence == "reaction-dataset":
        return "strong"
    if existence == "pubchem":
        return "weak"
    return "none"


def svg_of(smi: str, cache: Dict[str, str], *, width: int = 220, height: int = 160) -> str:
    if smi in cache:
        return cache[smi]
    try:
        cache[smi] = smiles_to_svg(smi, width=width, height=height)
    except Exception:
        cache[smi] = ""
    return cache[smi]


def mean_sims(sims: Any) -> Optional[float]:
    vals = [float(x) for x in (sims or []) if isinstance(x, (int, float))]
    if not vals:
        return None
    return sum(vals[:5]) / min(5, len(vals))


def forward_eff(vt: dict) -> tuple[float, bool]:
    raw = vt.get("F_raw")
    if not isinstance(raw, (int, float)):
        return 0.0, False
    s = vt.get("S")
    n_r = int(vt.get("nR") or 1)
    eff = float(raw)
    floor = False
    if isinstance(s, (int, float)) and s >= 0.9:
        if eff < 0.3:
            floor = True
        eff = max(eff, 0.3)
    if n_r == 1 and isinstance(s, (int, float)):
        eff = max(eff, float(s) * float(s))
    return eff, floor


def dump_to_path(obj: dict, a_of: Optional[dict] = None) -> list:
    steps = []
    for node in walk(obj):
        vt = dict(node.get("v4_trace") or {})
        raw = rxn_of(node)
        if a_of and raw:
            known = bool(node.get("known_reaction"))
            if a_of.get("__identity__"):
                rec = a_of.get(f"{1 if known else 0}\t{raw}")
            else:
                rec = a_of.get(raw)
            if rec:
                vt.update(rec)
        a = vt.get("A")
        steps.append(
            SimpleNamespace(
                target=target_of(node),
                known_reaction=bool(node.get("known_reaction")),
                v4_trace=vt,
                unbaise_step_score=a if isinstance(a, (int, float)) else None,
            )
        )
    return steps


def annotate_route(obj: dict, *, a_of: Optional[dict] = None, memb: Optional[dict] = None) -> float:
    memb = memb or {}
    path = dump_to_path(obj, a_of)
    root = path[0].target if path else None
    logs, audits = try_path_local_str_audits(path, root=root, membership_by_smi=memb)
    if logs is None:
        audits = {}
        logs = route_logS_from_steps(path)
    for node, step in zip(walk(obj), path):
        node["_vt"] = dict(step.v4_trace or {})
        node["_audit"] = dict(audits.get(id(step)) or {})
    return float(logs)


def collect_smiles(obj: dict) -> set[str]:
    bag: set[str] = set()
    for node in walk(obj):
        smi = target_of(node)
        if smi:
            bag.add(smi)
        for r in reactants_of(node):
            bag.add(r)
    return bag


def _canon_smi(smi: str) -> str:
    if not smi:
        return ""
    try:
        from rdkit import Chem

        mol = Chem.MolFromSmiles(smi)
        if mol is not None:
            return Chem.MolToSmiles(mol)
    except Exception:
        pass
    return smi


def _canon_key(smi: str) -> str:
    return _canon_smi(smi) or smi


def unique_smiles(smiles: Iterable[str], *, already: Optional[set] = None) -> List[str]:
    """Drop tautomer/Kekulé duplicates. Keep first SMILES for each canon."""
    seen = set(already or ())
    out: List[str] = []
    for smi in smiles:
        if not smi:
            continue
        key = _canon_key(smi)
        if key in seen:
            continue
        seen.add(key)
        out.append(smi)
    return out


def prefer_catalog_smi(smi: str, buyable_ids: Optional[set] = None) -> str:
    if not smi:
        return smi
    if not buyable_ids:
        return smi
    if smi in buyable_ids:
        return smi
    canon = _canon_smi(smi)
    if canon and canon in buyable_ids:
        return canon
    return smi


def bbl_buyable_ids(obj: dict) -> set[str]:
    """Search-time BBL hits. Prefer dump bbl_leaves over a second catalog lookup."""
    out: set[str] = set()
    for item in obj.get("bbl_leaves") or []:
        smi = item.get("smiles") if isinstance(item, dict) else item
        if not smi:
            continue
        out.add(smi)
        canon = _canon_smi(smi)
        if canon:
            out.add(canon)
    return out


def _leaf(smi: str, svg_cache: dict, memb: dict, *, buyable: Optional[bool] = None) -> dict:
    rec = {
        "kind": "leaf",
        "smiles": smi,
        "svg": svg_of(smi, svg_cache),
        "known": False,
        "molecule_existence": existence_of(smi, memb),
        "children": [],
    }
    if buyable is True:
        rec["buyable"] = True
    elif buyable is False:
        rec["buyable"] = False
        rec["open"] = True
    return rec


def _leaf_buyable(
    smi: str,
    *,
    buyable_leaves: Optional[bool],
    buyable_fn,
    buyable_ids: Optional[set] = None,
) -> Optional[bool]:
    if buyable_ids and (smi in buyable_ids or _canon_smi(smi) in buyable_ids):
        return True
    if buyable_fn is not None and buyable_fn(smi):
        return True
    if is_search_inorganic(smi):
        return True
    # Complete dumps: search already accepted leftover reactants.
    if buyable_leaves is True:
        return True
    if buyable_leaves is False:
        return False
    return None


def convert_node(
    node: dict,
    depth: int,
    svg_cache: dict,
    memb: dict,
    *,
    buyable_leaves: Optional[bool] = None,
    buyable_fn=None,
    buyable_ids: Optional[set] = None,
) -> dict:
    smi = target_of(node)
    rxn = rxn_of(node)
    kids = children_of(node)
    if ">>" not in rxn:
        return _leaf(
            smi,
            svg_cache,
            memb,
            buyable=_leaf_buyable(
                smi,
                buyable_leaves=buyable_leaves,
                buyable_fn=buyable_fn,
                buyable_ids=buyable_ids,
            ),
        )

    child_nodes = [
        convert_node(
            ch,
            depth + 1,
            svg_cache,
            memb,
            buyable_leaves=buyable_leaves,
            buyable_fn=buyable_fn,
            buyable_ids=buyable_ids,
        )
        for ch in kids
    ]
    shown = {_canon_key(c.get("smiles") or "") for c in child_nodes if c.get("smiles")}
    leftover = [
        prefer_catalog_smi(r, buyable_ids)
        for r in unique_smiles(reactants_of(node), already=shown)
    ]
    make = lambda r: _leaf(
        r,
        svg_cache,
        memb,
        buyable=_leaf_buyable(
            r,
            buyable_leaves=buyable_leaves,
            buyable_fn=buyable_fn,
            buyable_ids=buyable_ids,
        ),
    )
    if not child_nodes:
        child_nodes = [make(r) for r in leftover]
    else:
        child_nodes.extend(make(r) for r in leftover)

    vt = dict(node.get("_vt") or node.get("v4_trace") or {})
    audit = dict(node.get("_audit") or {})
    known = bool(node.get("known_reaction") or vt.get("is_known") or audit.get("known"))
    e = audit.get("E")
    if not isinstance(e, (int, float)):
        e = vt.get("E")
    cov = audit.get("coverage") or vt.get("coverage") or "none"
    f_eff, floor = forward_eff(vt)
    f_raw = vt.get("F_raw")
    s = vt.get("S")
    sa = vt.get("SA")
    return {
        "kind": "reaction",
        "smiles": smi,
        "svg": svg_of(smi, svg_cache),
        "known": known,
        "depth": int(audit.get("depth") if audit.get("depth") is not None else depth),
        "reaction_id": vt.get("canonical_rxn") or rxn,
        "new_step_score": e if isinstance(e, (int, float)) else None,
        "forward_raw_probability": f_raw if isinstance(f_raw, (int, float)) else None,
        "forward_probability": f_eff,
        "forward_floor_applied": floor,
        "similarity_factor": s if isinstance(s, (int, float)) else None,
        "similarity_mean": mean_sims(vt.get("top5_sims")),
        "synth_penalty_factor": sa if isinstance(sa, (int, float)) else None,
        "product_synthscore_max": vt.get("P_max"),
        "reactant_synthscore_max": vt.get("R_max"),
        "soft_coverage_class": cov if cov in ("strong", "weak") else "none",
        "soft_terminal_class": terminal_class(smi, memb),
        "molecule_existence": existence_of(smi, memb),
        "children": child_nodes,
    }


def count_steps(tree: dict) -> tuple[int, int]:
    n = 0
    known = 0
    stack = [tree]
    while stack:
        node = stack.pop()
        if node.get("kind") == "reaction":
            n += 1
            if node.get("known"):
                known += 1
        stack.extend(node.get("children") or [])
    return n, known


def convert_route(
    obj: dict,
    *,
    svg_cache: dict,
    memb: dict,
    a_of: Optional[dict] = None,
    log_s: Any = None,
    score0: Any = None,
    pills: Optional[List[str]] = None,
    elapsed_sec: Any = None,
    elapsed_note: Optional[str] = None,
    buyable_leaves: Optional[bool] = None,
    buyable_fn=None,
    buyable_ids: Optional[set] = None,
) -> dict:
    computed = annotate_route(obj, a_of=a_of, memb=memb)
    ids = set(buyable_ids or ()) | bbl_buyable_ids(obj)
    tree = convert_node(
        obj,
        0,
        svg_cache,
        memb,
        buyable_leaves=buyable_leaves,
        buyable_fn=buyable_fn,
        buyable_ids=ids or None,
    )
    _warn_tree_invariants(tree, ids, label=target_of(obj) or "?")
    steps, known = count_steps(tree)
    rec = {
        "new_log_score": float(log_s) if isinstance(log_s, (int, float)) else computed,
        "old_score0": score0 if isinstance(score0, (int, float)) else obj.get("score0"),
        "steps": steps,
        "known_steps": known,
        "pills": list(pills or []),
        "tree": tree,
    }
    if isinstance(elapsed_sec, (int, float)):
        rec["elapsed_sec"] = float(elapsed_sec)
    if elapsed_note:
        rec["elapsed_note"] = elapsed_note
    return rec


def fetch_membership(smiles: Iterable[str]) -> dict:
    uniq = [s for s in dict.fromkeys(smiles) if s]
    if not uniq:
        return {}
    return try_membership_batch(uniq)


def sibling_canon_dups(tree: dict) -> list[str]:
    found: list[str] = []

    def rec(node: dict, path: str) -> None:
        kids = node.get("children") or []
        seen: dict[str, str] = {}
        for i, ch in enumerate(kids):
            smi = ch.get("smiles") or ""
            key = _canon_key(smi)
            if key and key in seen:
                found.append(f"{path} same-layer {key} ({seen[key]} vs {ch.get('kind')})")
            elif key:
                seen[key] = str(ch.get("kind") or "?")
            rec(ch, f"{path}.{i}")

    rec(tree, "root")
    return found


def missing_bbl_leaves(tree: dict, buyable_ids: Optional[set]) -> list[str]:
    if not buyable_ids:
        return []
    have: set[str] = set()

    def rec(node: dict) -> None:
        if node.get("kind") == "leaf" and node.get("buyable"):
            have.add(_canon_key(node.get("smiles") or ""))
        for ch in node.get("children") or []:
            rec(ch)

    rec(tree)
    missing: list[str] = []
    checked: set[str] = set()
    for smi in buyable_ids:
        key = _canon_key(smi)
        if not key or key in checked:
            continue
        checked.add(key)
        if key not in have:
            missing.append(key)
    return missing


def _warn_tree_invariants(tree: dict, buyable_ids: Optional[set], *, label: str) -> None:
    dups = sibling_canon_dups(tree)
    miss = missing_bbl_leaves(tree, buyable_ids)
    if dups:
        print(f"# tree-check FAIL {label}: sibling dups {dups}", flush=True)
    if miss:
        print(f"# tree-check WARN {label}: bbl_leaves not a buyable leaf {miss}", flush=True)


def write_site(out: Path, payload: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "styles.css", "app.js"):
        shutil.copy2(ASSETS / name, out / name)
    (out / "data.js").write_text(
        "window.ROUTE_COMPARE_DATA=" + json.dumps(payload, ensure_ascii=False, default=str) + ";\n",
        encoding="utf-8",
    )


def _load_route(spec: Any, base: Path) -> dict:
    if isinstance(spec, dict) and spec.get("path"):
        return json.loads((base / spec["path"]).read_text())
    if isinstance(spec, dict) and spec.get("obj"):
        return spec["obj"]
    if isinstance(spec, str):
        return json.loads((base / spec).read_text())
    raise ValueError(f"route spec needs path or obj: {spec!r}")


def build_from_manifest(
    manifest: dict,
    *,
    base: Path,
    a_of: Optional[dict],
    memb: Optional[dict],
    buyable_fn=None,
) -> dict:
    svg_cache: dict[str, str] = {}
    smiles: set[str] = set()
    loaded: list[tuple[dict, dict]] = []
    for case in manifest.get("cases") or []:
        raw_routes = {}
        for slot_id, spec in (case.get("routes") or {}).items():
            if isinstance(spec, dict) and spec.get("empty"):
                raw_routes[slot_id] = (spec, None)
                continue
            obj = _load_route(spec, base)
            raw_routes[slot_id] = (spec if isinstance(spec, dict) else {}, obj)
            smiles |= collect_smiles(obj)
            tgt = target_of(obj)
            if tgt:
                smiles.add(tgt)
        loaded.append((case, raw_routes))
    if memb is None:
        memb = fetch_membership(smiles)
    cases = []
    for case, raw_routes in loaded:
        routes = {}
        for slot_id, (spec, obj) in raw_routes.items():
            if obj is None:
                empty = {
                    "tree": None,
                    "status": "empty",
                    "empty_reason": spec.get("empty") if isinstance(spec, dict) else "没有可画的路线",
                    "pills": list(spec.get("pills") or []) if isinstance(spec, dict) else [],
                }
                if isinstance(spec, dict) and isinstance(spec.get("elapsed_sec"), (int, float)):
                    empty["elapsed_sec"] = float(spec["elapsed_sec"])
                if isinstance(spec, dict) and spec.get("elapsed_note"):
                    empty["elapsed_note"] = spec["elapsed_note"]
                routes[slot_id] = empty
                continue
            routes[slot_id] = convert_route(
                obj,
                svg_cache=svg_cache,
                memb=memb,
                a_of=a_of,
                log_s=spec.get("logS") if isinstance(spec, dict) else None,
                score0=spec.get("score0") if isinstance(spec, dict) else None,
                pills=spec.get("pills") if isinstance(spec, dict) else None,
                elapsed_sec=spec.get("elapsed_sec") if isinstance(spec, dict) else None,
                elapsed_note=spec.get("elapsed_note") if isinstance(spec, dict) else None,
                buyable_leaves=(
                    spec.get("buyable_leaves") if isinstance(spec, dict) else None
                ),
                buyable_fn=buyable_fn,
            )
        first = next((obj for _spec, obj in raw_routes.values() if obj), {}) or {}
        smi = case.get("target_smiles") or target_of(first)
        cases.append(
            {
                "target_id": case.get("target_id") or "case",
                "target_smiles": smi,
                "target_svg": svg_of(smi, svg_cache, width=280, height=180) if smi else "",
                "target_molecule_existence": existence_of(smi, memb),
                "metrics": list(case.get("metrics") or []),
                "downloads": list(case.get("downloads") or []),
                "routes": routes,
            }
        )
    payload = {k: v for k, v in manifest.items() if k != "cases"}
    payload.setdefault("schema_version", "retro-route-compare/compact-ltree-v1")
    payload["cases"] = cases
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a compact L-tree route comparison site.")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--payload", help="Prebuilt ROUTE_COMPARE_DATA JSON")
    parser.add_argument("--manifest", help="Manifest JSON with slots + cases[].routes[id].path")
    parser.add_argument("--a-cache", dest="a_cache", help="Optional raw-rxn → v4 fields JSON")
    parser.add_argument("--membership", help="Optional smiles → membership JSON")
    parser.add_argument("--bbl", help="Optional BBL pkl/tsv used by search is_material")
    parser.add_argument("--max-price", dest="max_price", type=float, default=3000)
    args = parser.parse_args()
    out = Path(args.out)
    if args.payload:
        payload = json.loads(Path(args.payload).read_text())
    elif args.manifest:
        man_path = Path(args.manifest)
        manifest = json.loads(man_path.read_text())
        a_of = json.loads(Path(args.a_cache).read_text()) if args.a_cache else None
        memb = json.loads(Path(args.membership).read_text()) if args.membership else None
        buyable_fn = try_bbl_buyable_fn(args.bbl, max_price=args.max_price)
        payload = build_from_manifest(
            manifest,
            base=man_path.parent,
            a_of=a_of,
            memb=memb,
            buyable_fn=buyable_fn,
        )
    else:
        parser.error("pass --payload or --manifest")
    write_site(out, payload)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
