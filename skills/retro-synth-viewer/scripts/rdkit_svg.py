"""RDKit MolDraw2DSVG for inline molecule drawings. Optional: rdkit."""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=4096)
def smiles_to_svg(smiles: str, width: int = 220, height: int = 160) -> str:
    if not smiles or "*" in smiles:
        return _placeholder_svg(width, height, "?")
    try:
        from rdkit import Chem
        from rdkit.Chem import rdCoordGen
        from rdkit.Chem.Draw import rdMolDraw2D
    except ImportError:
        return _placeholder_svg(width, height, "no RDKit")

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return _placeholder_svg(width, height, "invalid")
    try:
        rdCoordGen.AddCoords(mol)
    except Exception:
        pass

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.bondLineWidth = 1.5
    opts.padding = 0.1
    opts.addStereoAnnotation = True
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    if "<?xml" in svg:
        svg = svg.split("?>", 1)[-1].strip()
    return svg


def _placeholder_svg(w: int, h: int, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">'
        f'<rect width="100%" height="100%" fill="#f5f5f5" stroke="#ccc"/>'
        f'<text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" '
        f'font-size="12" fill="#888">{label}</text></svg>'
    )
