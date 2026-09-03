---
name: retro-experiment-matrix
description: >-
  Run Retro Engine local experiment matrices (prod ∥ reactseq stacks) with
  mandatory smoke gates, PYTHONPATH/refmap warm safety, checkpoint resume, and
  long-run stability checks. Use when starting, resuming, or debugging
  run_local_prod_reactseq_matrix / rerun_reactseq_matrix_proc_isolated /
  bh_full_matrix campaigns, or when the user mentions experiment matrix,
  S0/S1/S2/S3 stacks, topo, refmap, or matrix resume.
---

# Retro Experiment Matrix

Operate **local** hypergraph matrices under `artifacts/bh_full_matrix/`.  
Do **not** confuse with moltrek→r3s HTTP prod matrices.

## Canonical entrypoints

| Script | Role |
|--------|------|
| `scripts/run_local_prod_reactseq_matrix.py` | Single-process matrix runner (`--stacks`, `--backends`, `--resume`, `--ref-pkl`) |
| `scripts/rerun_reactseq_matrix_proc_isolated.sh` | **One fresh Python process per stack**, reactseq-only (avoids Infrastructure `@Singleton` reuse after prod warm) |
| `scripts/queue_local_prod_reactseq_matrix.sh` | Full campaign queue (phase gates + mem guard) |
| `artifacts/.../EXPERIMENT_MATRIX.md` | Stack × backend contract |

Default isolated out: `artifacts/bh_full_matrix/reactseq_proc_isolated/`  
Default paired out: `artifacts/bh_full_matrix/local_prod_reactseq_matrix/`

## Stack semantics (memorize)

| Stack | TOPO | REFMAP | Ref library |
|-------|:----:|:------:|-------------|
| `S0_baseline` | 0 | 0 | default `production/models/ref.pkl.gz` (import-time / live) |
| `S1_topo` | **1** | 0 | same as S0 |
| `S2_topo_refmap` | **1** | **1** | same + **atom-map / multi-product component index** |
| `S3_newref` | 0 | 0 | **`ref_from_mapping_embed_ok.pkl.gz`** via `--ref-pkl` |
| `S3_newref_topo_refmap` | **1** | **1** | new ref + topo + refmap |

Contrasts:
- **S0 vs S1** = topo-only (edge topology dedup). Often **no coverage change** if winning paths never collided on topo keys.
- **S0 vs S3** = **library-only** (old ref vs mapping-built new ref). Same search flags.
- **S2 / S3tr** = enable `RETRO_REF_MAP_OPT` (atom mapping + main-product component index). **Not** enabled by “new library” alone.

## Hard rules before a full matrix

### 1) Smoke run (mandatory)

Never launch a full 119-cell stack until smoke passes:

```bash
cd /home/ubuntu/retro-engine
export PYTHONPATH="$PWD/c12_search:$PWD/C12Translator:$PWD/bronze${PYTHONPATH:+:$PYTHONPATH}"
export RETRO_MATRIX_OUT="${RETRO_MATRIX_OUT:-$PWD/artifacts/bh_full_matrix/matrix_smoke}"
mkdir -p "$RETRO_MATRIX_OUT"

# A) Import / refmap warm (stacks with REFMAP=1)
RETRO_REF_MAP_OPT=1 RETRO_REF_PKL=$PWD/production/models/ref.pkl.gz \
  /home/ubuntu/miniconda3/envs/forward/bin/python -c "
import sys, os, time
from pathlib import Path
REPO=Path('.').resolve()
sys.path[:0]=[str(REPO/'c12_search'),str(REPO/'C12Translator'),str(REPO/'bronze')]
from c12_search.ref_service.ref_map_opt import ensure_component_index
t=time.time(); idx=ensure_component_index(); print('index', len(idx), 'in', round(time.time()-t,1),'s')
"

# B) 1–2 cell end-to-end (use --resume safe out dir)
# Prefer isolated script for reactseq-only:
bash scripts/rerun_reactseq_matrix_proc_isolated.sh \
  --out "$RETRO_MATRIX_OUT" \
  --stacks S0_baseline
# Then interrupt after 1–2 completes OR run python with a tiny cohort if available.
```

Smoke must show:
1. **No import / PYTHONPATH errors** (especially `c12_search` on refmap warm)
2. ReactSeq warm loads real HF weights (**warm ≳ 30s**, not `0.0s`)
3. `max_new_tokens` for ReactSeq stays **200** (not clamped to 54 — that means Singleton prod reuse)
4. Cell finishes `complete` or clean `no_route` (not instant root wipe from wrong backend)

### 2) Long-run stability

- Prefer **`rerun_reactseq_matrix_proc_isolated.sh`** when measuring reactseq (one process per stack).
- Keep `RETRO_ONLINE_MRP=1`, soft fuse on; optional `mem_guard_matrix.sh`.
- Log to a dedicated `rerun_queue.log` / `matrix.log`; do not share GPU with another matrix.
- Confirm `nohup` / systemd / screen so SSH drop does not kill the run.

### 3) Checkpoint resume

- Always pass **`--resume`** (default in isolated script).
- Resume key = cell already present in `cell_results.json` with a terminal `solved_status`.
- After a crash: fix root cause → re-invoke **same `--out`** and stack list; completed cells skip.
- If a stack failed at warm (0 cells written), fix then re-run **that stack only**.

## PYTHONPATH / refmap footgun

`_warm_ref_index_if_needed()` must insert `c12_search` on `sys.path` **before** importing `ref_map_opt` (fixed in `run_local_prod_reactseq_matrix.py`).  
Also export:

```bash
export PYTHONPATH="$REPO/c12_search:$REPO/C12Translator:$REPO/bronze${PYTHONPATH:+:$PYTHONPATH}"
```

Symptom of regression: S2 / S3tr dies in &lt;1s with `ModuleNotFoundError: c12_search`.

## ReactSeq Singleton footgun

Same process: warm `prod_local` then `reactseq_four_model` → `@Singleton` reuses prod Infrastructure → mass `no_route`.  
**Fix:** process-per-stack isolated rerun (never alternate backends in one PID for fair reactseq numbers).

## Operator checklist

```
[ ] Read EXPERIMENT_MATRIX.md for intended contrasts
[ ] Smoke import + 1–2 cells
[ ] Confirm backend/token clamp / warm time
[ ] Launch with --resume and dedicated OUT
[ ] Monitor matrix.log progress N/119
[ ] On failure: classify warm vs cell vs OOM; fix; resume same OUT
[ ] Update campaign / noroute gap reports after stack completion
```

## Updating reports

- Gap page: `artifacts/bh_full_matrix/reactseq_proc_isolated/reports/noroute_gap_20260727/`
- Campaign: `.../local_prod_reactseq_matrix/reports/campaign_report_20260727/`
- Compare fair arms: **same stack** RS vs prod (same ref).  
  Isolated S0/S1 use **default old ref**; only S3_* apply `--ref-pkl`.  
  Do **not** call isolated-S0 vs prod-S3 “same library”.

## When user asks “is the matrix done?”

1. `pgrep -af run_local_prod_reactseq_matrix|rerun_reactseq`
2. `cell_results.json` → per-stack `Counter(solved_status)` and `len(cells)/119`
3. Tail `matrix.log` for `N/119` and `<<< stack=`
