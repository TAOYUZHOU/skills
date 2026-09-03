# Scoring-route data schema

Emitted as `window.ROUTE_COMPARE_DATA` in `data.js`.

## Top-level

```json
{
  "schema_version": "retro-route-compare/compact-ltree-v1",
  "title": "...",
  "eyebrow": "...",
  "lede": "...",
  "formula": "logS = Σ (1+2^{-d}) ln(E)",
  "survey": false,
  "slots": [
    {"id": "dual", "kicker": "Dual-queue", "title": "Dual dump top1", "accent": "new"}
  ],
  "cases": []
}
```

`accent`: `new` (teal), `old` (gray), `alt` (blue).

Panels always stack as **full-width rows**. Do not use `slots-2` / `slots-3` as multi-column layout.

## Manifest (`--manifest`)

`path` is relative to the manifest file.

```json
{
  "title": "Dual vs patent",
  "slots": [
    {"id": "dual", "kicker": "Dual", "title": "dump top1", "accent": "new"}
  ],
  "cases": [
    {
      "target_id": "M089",
      "metrics": ["Dual logS −17.65"],
      "routes": {
        "dual": {"path": "M089_dual.json", "logS": -17.65, "score0": 0.01, "pills": ["i=0"]}
      }
    }
  ]
}
```

## Case (in `data.js`)

```json
{
  "target_id": "M089",
  "target_smiles": "C...",
  "target_svg": "<svg>...</svg>",
  "target_molecule_existence": "none",
  "metrics": ["Dual logS −17.65"],
  "downloads": [{"href": "downloads/M089_dual.json", "label": "Dual JSON"}],
  "routes": {
    "dual": {
      "new_log_score": -17.65,
      "old_score0": 0.012,
      "steps": 9,
      "known_steps": 2,
      "pills": ["dump i=0"],
      "elapsed_sec": 208.45,
      "elapsed_note": null,
      "tree": {}
    }
  }
}
```

## Tree node

Reaction (`kind: "reaction"`):

| Field | Source |
|---|---|
| `smiles` | product / `TargetMol` |
| `svg` | RDKit inline SVG |
| `known` | `known_reaction` |
| `depth` | 0 = reaction that makes the case target |
| `reaction_id` | `v4_trace.canonical_rxn` or raw `Formula`/`rxn` |
| `new_step_score` | path-local `E` (step) |
| `forward_raw_probability` | `F_raw` |
| `forward_probability` | `F_eff` after sim03 floor / single-reactant `S²` |
| `forward_floor_applied` | true when sim03≥0.9 and raw&lt;0.3 |
| `similarity_factor` | `S` (sim03) |
| `similarity_mean` | mean of `top5_sims` |
| `synth_penalty_factor` | `SA` |
| `product_synthscore_max` / `reactant_synthscore_max` | `P_max` / `R_max` |
| `soft_coverage_class` | path-local STR: `strong` / `weak` / `none` |
| `soft_terminal_class` | product membership tier |
| `molecule_existence` | `reaction-dataset` / `pubchem` / `none` |
| `children` | reactant nodes (further reactions or leaves) |

Route-level `elapsed_sec` is the search wall of that molecule×arm (not per top-k).
Optional `elapsed_note` when there is no finite time (unbounded / stopped).
The viewer pill is `推理 …s`.
A first_solve slot should set `elapsed_sec` to the wall when the first solved route closed, not the full-run \(T\).
Future Dual runs also write `{stem}_first_solve.txt` at first close (`RETRO_DUMP_FIRST_SOLVE=1`). The 2026-08-26 campaign only kept score-sorted `output_topk=100`, so vanished first-depth trees cannot be recovered.

Leaf (`kind: "leaf"`): `smiles`, `svg`, `molecule_existence`, optional `buyable` / `open`.
Green when the **search BBL** accepted it. Prefer dump `bbl_leaves` (HTTP stock /
inorganic) over a second local catalog lookup — SMILES form and stock can differ.
0-carbon inorganics stay green. Dashed orange only if that leaf is **not** in BBL.
Membership ≠ purchasable. In CSS, `.leaf.buyable` green outranks purple/cyan/gray
**and** `.open-leaf`.

### Leftover reactants (required)

`Formula` is often Kekulé; `OriFormula` / `main_material` / `bbl_leaves` are aromatic.
`reactants_of` prefers `OriFormula`. After children are converted, leftover =
reactants whose **RDKit canon** is not already a sibling (reaction product or leaf).
Do not compare raw strings. Do not append a leftover of a molecule that this
parent already expanded. Prefer the catalog SMILES form when it is in `bbl_leaves`.

Same-layer duplicate canons are a converter bug. The builder prints them.

## Raw trees

Walk `Children` or `children`. Reaction if `Formula`/`rxn` contains `>>`.
Empty `Children` is still a reaction — synthesize leaf children from reactants
(`scripts/route_parse.py`).

If a packed tree has no `v4_trace`, pass `--a-cache` (raw rxn → `{A,S,SA,F_raw,...}`).
If `c12_search` is installed as a package, the builder uses `path_local_str_audits`;
otherwise it uses `scripts/v4_local.py`.

## Difference highlight

A reaction (plus its immediate children) is highlighted when its `reaction_id`
does not appear in **any other** slot of the same case.

## Survey

Optional. If `survey` is missing/false, the questionnaire is omitted.
