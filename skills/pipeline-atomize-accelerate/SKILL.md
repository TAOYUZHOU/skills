---
name: pipeline-atomize-accelerate
description: >-
  Engineer pipeline speedups via resident processes, recursive atomization
  with continuous stream, and a preflight Pareto solver over FLOPS / RAM /
  VRAM. Use when accelerating multi-stage inference or search, splitting a
  bottleneck, overlapping GPU/CPU/HTTP, writing a wall-clock Gantt model,
  choosing batch/fill/worker knobs, or asking whether a program is already
  theoretically efficient or on the hardware Pareto front.
metadata:
  short-description: Resident IO, atomize-to-unsplittable, preflight Pareto
---

# Pipeline Atomize Accelerate

通用工程加速：先消重复 IO，再按资源原子化并连续 stream，把瓶颈递归拆到不能再拆，最后用硬件容量求解 Pareto。未到这一步，禁止宣称「已经最优」。

## When to use

- 多阶段推理 / 搜索 / ETL 觉得慢，或要选 batch、fill、worker、overlap
- 用户提到常驻进程、原子化、stream、Gantt、preflight、Pareto、FLOPS / 显存
- 要写加速数学模型的 HTML，或判断「还能不能再拆」

Related: job *queues* of independent trainings → `resource-aware-queue-scheduler`.
Publish the HTML → `public-html-report`.

## 三条硬原则（verbatim）

1. **常驻进程降低多次推理重复IO**
2. **复杂程序原子化拆分进程，考虑连续stream，递归式拆解瓶颈进程，直到瓶颈进程无法再拆，说明程序做到了理论上效率最优，需要构建对应的数学模型并写到对应html文档**
3. **复杂程序需要有preflight调度器，把数学模型写成一个求解器，可以根据硬件具体的flops，内存，显存大小，计算Pareto前沿参数配置**

## Agent workflow

Copy and tick:

```
Pipeline accelerate:
- [ ] Inventory jobs + unary resources (do not invent independent CPUs)
- [ ] Resident: kill repeated weight / tokenizer / session / DB IO
- [ ] Atomize each composite stage; stream across resources
- [ ] Recurse on the current bottleneck
- [ ] Stop only if bottleneck is atomic AND hardware-bound
- [ ] Write / update the model HTML (equations + STREAM Gantt)
- [ ] Run scripts/preflight_solver.py with this host's FLOPS/RAM/VRAM
- [ ] Verdict: theoretically efficient? on capacity Pareto? (usually no)
```

Read [references/model.md](references/model.md) before writing equations.
Ship the human-readable model as HTML; start from [docs/model.html](docs/model.html).
Case-study layout: [references/audit-template.md](references/audit-template.md).

### 1. Inventory

List every **job** (what work) and every **unary resource** (what cannot overlap with itself). Shared host CPU + a shared library (BBL, GIL, graph lock) is **one** lane `CPU_shared`, not two. HTTP and GPU are their own lanes if they do not consume that CPU.

A job is **atomic** when splitting it would change the hardware/protocol quantum (one kernel, one HTTP request, one locked graph write) or would only create interference \(\rho\gg 1\).

### 2. Resident processes

If the same weights, tokenizer, CUDA context, HTTP session, or index is loaded per call, make a **resident** process/pool and pass only IO variables (tensors, SMILES, request ids).

Do **not** resident-thread a single-writer mutation (graph expand). Put lookups on an IO queue; keep one owner thread for writes.

### 3. Atomize + stream + recurse

For the current critical path:

1. Split a composite job into atoms with explicit precedence \(a\prec b\).
2. **连续 stream**：资源 \(r\) 一空且先行满足，立刻发下一原子；禁止等整段 tile。
3. Schedule = list scheduling on unary lanes. Wall \(T=\max_r T_r\).
4. Bottleneck \(=\arg\max_r T_r\). If that job is still composite, split it and go to 1.
5. Halt when the bottleneck atom is unsplittable. That is **theoretical efficiency** for *this* resource set — not yet Pareto over knobs.

Illegal: stuffing non-GPU work into \(T_{\mathrm{gpu}}\); overlapping two jobs that share BBL/GIL and then fitting \(\rho\).

### 4. Model HTML (mandatory)

Write or refresh a standalone HTML page with: symbol table, precedence, unary Gantt, halt rule, and measured vs predicted \(T\). Use KaTeX. Visual bar from `public-html-report`. No host secrets.

### 5. Preflight solver

```bash
python scripts/preflight_solver.py \
  --pipeline examples/pipeline.retro-dual.json \
  --hardware examples/hardware.t4.json \
  --out /tmp/preflight.json
```

`--probe-hardware` fills FLOPS / RAM / VRAM from this machine when possible.
The solver enumerates knobs, drops infeasible (VRAM/RAM/optional FLOP-seconds), reports the Pareto front of \((\mathrm{flux},\,T,\,\mathrm{quality}?)\).

Do not apply a `model_*` star that assumes an unlanded schedule. Quote `implemented_*` separately.
One-round Gantt is the solver. Dual tree wall is `scripts/compose_search_volume.py` (fill budget × \(n_{\mathrm{iter}}\)); do not fold that into `preflight_solver.py`.

## Extra levers (after the three principles)

Work avoidance beats overlap. Structure-share copies. Batch the IO lane, not the writer. Treat quality (logS, solved) as a Pareto axis. Memory-bandwidth often binds before peak FLOPS. Little's law: concurrency \(=\lambda W\). Do not re-parallelize a measured \(\rho\gg 1\) pair.

## Halt verdict language

| Phrase | Allowed only when |
|---|---|
| 理论上效率最优 | Bottleneck job is atomic; further split is a new resource or a new algorithm |
| 已在硬件 Pareto | Solver front, **landed** schedule, measured \(T\) matches, capacity respected |
| 还没到 | Default. Name the next split |

## Additional resources

- [references/model.md](references/model.md) — equations
- [docs/model.html](docs/model.html) — canonical model page
- [references/audit-template.md](references/audit-template.md) — case-study HTML
- [scripts/preflight_solver.py](scripts/preflight_solver.py) — execute, do not rewrite
