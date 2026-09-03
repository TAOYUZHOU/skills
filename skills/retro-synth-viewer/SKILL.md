---
name: retro-synth-viewer
description: >-
  Build scoring-route comparison websites for retrosynthesis: compact L-connector
  trees, per-step score badges, known/unknown edges, molecule-existence borders,
  difference highlight, and rxn copy. Use when creating or refreshing Dual vs
  patent, BH pair/matrix, Top-1 rescoring, or any route-tree scoring site.
  Publishing (nginx, auth, fixed IP) is owned by skill public-html-report.
---

# Retro Synthesis Scoring-Route Viewer

Self-contained content pipeline for **scored retrosynthesis trees**.
Publish with **`public-html-report`**.

This skill directory is the package. Do not read sibling repos, host gold
sites, or project `scripts/` for assets or converters. Resolve this skill by
the folder that contains this `SKILL.md`.

## Gold contract (this package)

Required UX — implemented by `assets/app.js` + `assets/styles.css`:

| Feature | Rule |
|---|---|
| Layout | Compact contour-packed **L-connector** tree (`compactTreeLayout`). Panels **stack as full-width rows**. Never put 2/3/4 slots in narrow columns on wide screens. |
| Step badges | Reaction cards show **step / forward / sim03 / SA / STR** |
| Edges | Known = thick gold; unknown = thin gray |
| Molecule borders | BBL `is_material` leaf green (incl. 0-carbon like HCl/`Cl`); not-in-BBL leftover dashed orange; reaction-lib purple; PubChem cyan; unknown gray. Green outranks purple/cyan **and** dashed orange. Do not paint every leaf green, and do not paint a whole `no_route` tree orange. |
| Diff highlight | Pale-red fill on reactions unique to that panel. Identical reaction sets get a 「同路，只是分数不同」 pill instead of red. |
| Step number | Click → popover + copy `reactants>>product` |
| Nav | Sticky case select, prev/next, per-panel zoom |
| Search wall | Each panel shows **推理时间** (`elapsed_sec` / `elapsed_note`). Time is per molecule×arm, shared by top-k of that run. Empty panels still show it (e.g. ≥2h 被停). Optional `dual_first` / first_solve slot uses \(t\) at first `SEARCH_TRACE` with `solved>0`, not the full-run \(T\). |
| Legend | Scorer rules in a `<details>` block |

Do **not** ship nested UL trees, pill-only stats without badges, or raw host paths.

## Hard rules — leftover + 绿框（do not regress）

These failed in production once. The next rebuild must not.

1. **Never match leftover reactants by raw SMILES.** Dual dumps keep Kekulé `Formula` / `TargetMol` next to aromatic `OriFormula` / `main_material` (`OC1=CC=CC=C1` vs `Oc1ccccc1`). Raw `r not in shown` duplicates the same molecule on one layer: an expanded reaction card plus a gray leftover, or two leaves of one BBL hit.
2. **Canon is the identity.** `unique_smiles` / leftover skip use RDKit `MolToSmiles`. Prefer `OriFormula` when splitting reactants so leftover SMILES match `bbl_leaves`. `get_reaction_from_smiles(..., main_material)` may append `main_material` even when the Kekulé tautomer is already on the left — canon-dedupe is mandatory after that.
3. **One card per canon per parent.** If a child reaction already shows product \(m\), do **not** also emit a leftover leaf of \(m\). Same-layer repeats are a converter bug, not a search feature.
4. **Green = search BBL, not membership.** `molecule_existence` purple/cyan ≠ purchasable. Set `buyable` from dump `bbl_leaves` (raw **and** canon), optional `--bbl` HTTP `is_material`, and 0-carbon inorganics. Rebuild Dual dumps with `--bbl http://…` when the search BBL is HTTP. A leftover that is only in the reaction dataset stays purple unless BBL accepted it.
5. **CSS:** `.leaf.buyable` must come **after** `.open-leaf` and membership colors. Bump `styles.css?v=` on every visual fix.
6. **Build-time check.** After `convert_node`, refuse to stay silent: print same-layer canon dups and dump `bbl_leaves` that did not become a `buyable` leaf. Investigate before publishing.
7. **Verify before calling the site done.** Walk every tree: zero same-canon siblings; every dump `bbl_leaves` SMILES has a green leaf; leftover intermediates of expanded children are gone. A screenshot is not this check.

## Build

```bash
# SKILL = directory that contains this SKILL.md
python "$SKILL/scripts/build_route_compare_site.py" \
  --out "$OUT" \
  --manifest manifest.json
# or, if ROUTE_COMPARE_DATA is already built:
python "$SKILL/scripts/build_route_compare_site.py" \
  --out "$OUT" \
  --payload payload.json
```

`--manifest` cases point at route JSON files (`path` relative to the manifest).
Optional `--a-cache` overlays per-reaction v4 fields; `--membership` supplies
molecule existence. For Dual dumps pass `--bbl <search BBL URL or pkl>` so leftover
leaves that HTTP stock accepted get `buyable` even when dump `bbl_leaves` used a
different SMILES form. Schema: [reference.md](reference.md).

Serve the **output directory only**, then follow `public-html-report`.

## Data contract

Minimum:

- `slots[]` — one panel each (`id`, `kicker`, `title`, `accent`)
- `cases[].routes[slot_id].tree` — nested `{kind, smiles, svg, known, children, ...}`
- Reaction nodes carry `new_step_score` (E), `forward_probability`, `similarity_factor` (S), `synth_penalty_factor` (SA), `soft_coverage_class` (STR)

Field map from Dual/v4 traces: `E`→step, `F_raw`→forward, `S`→sim03, `SA`→SA,
`coverage`→STR, `known_reaction`→known, `logS_route`→route logS.

## Package files

| File | Role |
|---|---|
| `assets/app.js` | N-slot viewer (L-tree, badges, popover, zoom) |
| `assets/styles.css` | Paper/teal skin |
| `assets/index.html` | Shell; panels built from `slots` |
| `scripts/build_route_compare_site.py` | Manifest/payload → site |
| `scripts/rdkit_svg.py` | SMILES → inline SVG (optional `rdkit`) |
| `scripts/route_parse.py` | Reaction SMILES split |
| `scripts/v4_local.py` | Local logS / STR; optional installed `c12_search` |

Python extras (not files): `rdkit` for drawings; `c12_search` only if already
installed as a package. Missing extras degrade (placeholder SVG, local logS).

## Publish

Follow **`public-html-report`**.
