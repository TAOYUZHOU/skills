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

Leaf (`kind: "leaf"`): `smiles`, `svg`, `molecule_existence`. CSS paints all leaves green (buyable / search-stop).

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
