# Case-study HTML

One page, visual bar from `public-html-report`. Sections in this order:

1. **Verdict** — theoretically efficient? capacity Pareto? one sentence each. Default is no.
2. **Lanes and jobs** — table: job, resource, atomic?, resident?, predecessors.
3. **Resident IO** — what is warm, what still reloads.
4. **Recursion log** — each bottleneck and whether it was split.
5. **STREAM Gantt** — landed schedule vs target vs any illegal fold, same time axis.
6. **Preflight** — host FLOPS / RAM / VRAM, feasible set, Pareto table. Mark unlanded rows.
7. **Measured** — live \(T\), \(J\), quality. Predicted vs live.
8. **Next split** — the one composite still on the critical path, or “halt”.

Do not dump absolute host paths or credentials.
