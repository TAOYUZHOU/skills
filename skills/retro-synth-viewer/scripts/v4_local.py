"""Path-local STR helpers. Self-contained; optional c12_search if installed as a package."""
from __future__ import annotations

import math
from typing import Any, Optional

E_LN_FLOOR = 1e-12


def depth_weight(d: int) -> float:
    return 1.0 + (2.0 ** (-int(d)))


def apply_str(A: float, coverage: str, is_known: bool) -> float:
    if is_known:
        return float(A)
    if A <= 0:
        return 0.0
    if coverage == "strong":
        return math.sqrt(A)
    if coverage == "weak":
        return A ** 0.75
    return float(A)


def route_logS_from_steps(steps: list) -> float:
    total = 0.0
    n = 0
    for d, step in enumerate(steps):
        vt = getattr(step, "v4_trace", None) or {}
        a = vt.get("A")
        if not isinstance(a, (int, float)):
            a = 0.0
        known = bool(getattr(step, "known_reaction", False))
        cov = (vt.get("coverage") or "none")
        e = apply_str(float(a), cov, known)
        e = e if e > 0 else E_LN_FLOOR
        total += depth_weight(d) * math.log(e)
        n += 1
    return total if n else 0.0


def try_path_local_str_audits(path: list, *, root: Optional[str], membership_by_smi: Optional[dict]) -> tuple[Optional[float], dict]:
    try:
        from c12_search.single_step.v4_formula import path_local_str_audits
    except Exception:
        return None, {}
    try:
        return path_local_str_audits(path, root=root, membership_by_smi=membership_by_smi)
    except Exception:
        return None, {}


def try_membership_batch(smiles: list[str]) -> dict[str, Any]:
    try:
        from c12_search.single_step.v4_score_apis import membership_batch
    except Exception:
        return {}
    try:
        return membership_batch(smiles) or {}
    except Exception:
        return {}
