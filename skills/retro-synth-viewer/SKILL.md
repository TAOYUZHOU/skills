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
| Layout | Compact contour-packed **L-connector** tree (`compactTreeLayout`) |
| Step badges | Reaction cards show **step / forward / sim03 / SA / STR** |
| Edges | Known = thick gold; unknown = thin gray |
| Molecule borders | Leaf green; reaction-lib purple; PubChem cyan; unknown gray |
| Diff highlight | Pale-red fill on reactions (and their reactants) unique to that panel |
| Step number | Click → popover + copy `reactants>>product` |
| Nav | Sticky case select, prev/next, per-panel zoom |
| Legend | Scorer rules in a `<details>` block |

Do **not** ship nested UL trees, pill-only stats without badges, or raw host paths.

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
molecule existence. Schema: [reference.md](reference.md).

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
