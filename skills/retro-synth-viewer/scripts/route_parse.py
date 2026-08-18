"""Parse moltrek/patent reaction SMILES. No repo imports."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple


def get_reaction_from_smiles(
    rxn: str,
    main_material: Optional[str] = None,
) -> Tuple[List[str], str]:
    rxn = (rxn or "").strip()
    if ">>" in rxn:
        left, right = rxn.split(">>", 1)
        if main_material:
            left = re.sub(re.escape(main_material), "", left).strip(".")
        reactants = [p for p in left.split(".") if p]
        if main_material:
            reactants.append(main_material)
        return reactants, right.strip()
    if rxn.count(">") >= 2:
        parts = rxn.split(">")
        reactants = []
        for part in parts[:-1]:
            reactants.extend(p for p in part.split(".") if p)
        return reactants, parts[-1].strip()
    return [], rxn
