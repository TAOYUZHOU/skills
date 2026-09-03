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


def carbon_count(smi: str) -> Optional[int]:
    try:
        from rdkit import Chem
    except Exception:
        return None
    mol = Chem.MolFromSmiles(smi or "")
    if mol is None:
        return None
    return sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() == 6)


def is_search_inorganic(smi: str) -> bool:
    """Same gate as c12 Bbl.is_material: 0 carbons count as buyable."""
    if not smi:
        return True
    n = carbon_count(smi)
    return n == 0


def try_bbl_buyable_fn(
    bbl_pkl: Optional[str] = None,
    max_price: float = 3000,
) -> Optional[Any]:
    """Return smiles → bool using search BBL. Inorganic always True."""
    finder = None
    if bbl_pkl:
        try:
            from c12_search.bbl_server.bbl_service import BblService

            class _Cfg:
                def get_bbl_config(self):
                    return {"url": bbl_pkl, "debug": False}

            svc = BblService(config0=_Cfg())

            def finder(smi: str) -> bool:
                hits = svc.find(
                    smi,
                    price_filter=lambda price: price <= max_price,
                )
                return bool(hits)
        except Exception:
            finder = None

    def is_buyable(smi: str) -> bool:
        if is_search_inorganic(smi):
            return True
        if finder is None:
            return False
        try:
            return bool(finder(smi))
        except Exception:
            return False

    return is_buyable


def try_membership_batch(smiles: list[str]) -> dict[str, Any]:
    try:
        from c12_search.single_step.v4_score_apis import membership_batch
    except Exception:
        return {}
    try:
        return membership_batch(smiles) or {}
    except Exception:
        return {}
