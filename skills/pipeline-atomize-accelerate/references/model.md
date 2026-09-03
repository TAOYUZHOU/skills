# Unary-resource stream model

## Objects

Resources \(\mathcal{R}=\{r\}\) are **unary** (capacity 1) unless the spec says otherwise.
Jobs \(j\) have a resource \(r(j)\) (this file used to write \(\rho(j)\); Dual already uses \(\rho\) for contention — do not mix), duration \(t_j\), predecessors \(\mathrm{Pred}(j)\), and optional working sets \(M_j\) (RAM), \(V_j\) (VRAM), \(F_j\) (FLOPs).

Precedence: \(a\prec b\) means \(\mathrm{end}(a)\le\mathrm{start}(b)\).
Unary: if \(r(a)=r(b)\) then their open intervals are disjoint.

## Contention \(\rho\) (independence)

\[
\rho_{a\parallel b}=\frac{t_a^{\parallel b}}{t_a^{\perp}}.
\]

\(t_a^{\perp}\) is the wall of \(a\) when it owns \(r(a)\). \(t_j\) in the Gantt is this isolated time. \(\rho=1\) means the independence assumption holds. \(\rho\gg 1\) means a hidden shared resource (cores, GIL, library, bandwidth). A ratio of medians is an estimator, not a per-tile constant.

GPU jobs still consume host cores. Write \(t_G=t_G^{\perp}\cdot\rho_G(\kappa_G)\), not \(t_G=t_{G,\mathrm{gpu}}\).

## Workers and core ratio \(\kappa\)

Atom time under one exclusive worker: \(t_j^{(1)}\). For \(n\) identical atoms, \(w\) workers, serial fraction \(\alpha\):

\[
T_j(w)=n\,t_j^{(1)}\Bigl(\alpha+\frac{1-\alpha}{w}\Bigr).
\]

\(\alpha=0\) is the linear model. It is valid only if each worker has exclusive cores and the job has no shared lock. Oversubscribe \(w>\kappa_j\) and the linear model is illegal.

Physical cores \(K\) are partitioned

\[
\kappa_G+\kappa_M+\kappa_E+\kappa_{\mathrm{OS}}=K.
\]

Generate-host needs \(\kappa_G\ge\kappa_G^{\min}\) or \(\rho_G\) rises. Expand is a single writer: extra \(\kappa_E\) does not shorten \(t_E\), it only protects \(t_G\) and \(t_E\). Mat workers \(w_M\le\min(B,\kappa_M)\). Objective remains \(J=n/T\). Enumerate integer \(\kappa\) and \(w\); keep the flux star **unlanded** until measured.

## Resident IO

Cold start \(T_{\mathrm{io}}^{\mathrm{cold}}\) paid once per process life.
Per-call residual \(T_{\mathrm{io}}^{\mathrm{hot}}\) (bytes on the wire / memcpy only).
After \(N\) calls the amortized load is \(T_{\mathrm{io}}^{\mathrm{cold}}/N+T_{\mathrm{io}}^{\mathrm{hot}}\).
Resident is justified when \(T_{\mathrm{io}}^{\mathrm{cold}}\) is comparable to useful work.

## Stream wall

List-schedule: start \(j\) at

\[
\mathrm{start}(j)=\max\Bigl(\max_{a\in\mathrm{Pred}(j)}\mathrm{end}(a),\;
\mathrm{free}(r(j))\Bigr).
\]

\[
T=\max_j\mathrm{end}(j)=\max_{r\in\mathcal{R}}T_r.
\]

Bottleneck \(\mathrm{bound}=\arg\max_r T_r\).
Throughput \(J=n/T\) for \(n\) payload units in the window.

## Recursion / halt

If \(\mathrm{bound}\) is a **composite** job, split it and reschedule.
Halt when the bound job is atomic. Then

\[
J\le J^\star=\min_r\mu_r,\qquad \mu_r=\frac{\text{payload on }r}{T_r}.
\]

\(J^\star\) is theoretical efficiency **for this \(\mathcal{R}\)**. It is not a knob Pareto.

## Illegal two-resource fold

Do not set \(T_{\mathrm{gpu}}:=A\cdot t_{\mathrm{lane}}\) while hiding decode / mat / HTTP in \(T_{\mathrm{drain}}\), and do not overlap two jobs that share a host library.

## Capacity

A knob vector \(\theta\) is feasible when

\[
\sum_j V_j(\theta)\le V_{\mathrm{cap}},\quad
\sum_j M_j(\theta)\le M_{\mathrm{cap}},\quad
\sum_j F_j(\theta)\le \Phi_{\mathrm{peak}}\cdot T(\theta)
\]

(the last is a lower bound: if measured \(T\) is already longer, the run is memory- or latency-bound, not FLOP-bound).

## Dual fill budget and tree wall

`fill` is **not** the GPU batch. \(B\) is one HF generate atom. `fill` is Dual's per-epoch hard cap: at most that many distinct unasked INIT, then `iterations += 1`.

\[
n_k=\min(\mathrm{fill},\,|U_k|),\qquad
n_{\mathrm{work}}=\sum_{k=1}^{n_{\mathrm{iter}}}n_k
\le \mathrm{mssr}\cdot\mathrm{fill}.
\]

\[
n_{\mathrm{iter}}=\min\bigl(\mathrm{mssr},\;\min\{k:|U_k|=0\}\bigr).
\]

One fill-round Gantt \(T_{\mathrm{round}}(B,\mathrm{fill})\) is what `preflight_solver.py` reports (\(A=\lceil\mathrm{fill}/B\rceil\)). The tree is

\[
T_{\mathrm{tree}}=n_{\mathrm{iter}}\,T_{\mathrm{round}}.
\]

\(n_{\mathrm{iter}}\) is endogenous: small \(B\) (more `plan_next_atom` per epoch) drains \(U_k\) sooner; large \(B\) or large `fill` commits stale VIP and keeps \(|U|\) fat. Measured on M098 at fill=32: \(n_{\mathrm{iter}}(4)=10\), \(n_{\mathrm{iter}}(8)=11\), \(n_{\mathrm{iter}}(16)=19\), \(n_{\mathrm{iter}}(32)=15\). Other fills are unlanded — quote only \(T_{\mathrm{round}}\) and the cap \(\mathrm{mssr}\cdot\mathrm{fill}\).

The solver executable stays one-round. Compose the tree with `compose_search_volume.py`.

Whole-tree \(T_{\mathrm{tree}}\) error is expected: \(n_{\mathrm{iter}}\) is endogenous and not known before the search. The quantity that should match is **fill-round flux**

\[
J=\frac{n}{T_{\mathrm{round}}},\qquad n=\min(\mathrm{fill},|U_k|).
\]

One-round Gantt error on M098 is ~7–11%. Do not judge the solver by \(T_{\mathrm{tree}}\) unless \(n_{\mathrm{iter}}\) was measured.

## Attach \(t_H\)

`schedule_three_lane` already serializes \(C,M,H,\mathrm{mrp}\) on \(\mathrm{CPU_{sh}}\). `tile_s[B].H` is attach per tile (easy ~0.06 s from hwopt; M101 ~0.2; M089 ~1.07). `evaluate()` adds \(H\) to each tile's `hots[k]` so it enters the Gantt. \(H\) is molecule/chirality/frontier state, not a function of \(|P|\) alone — a single table value is the easy-mol default.

Dynamic fill from task clock + accumulated score is a later algorithm. Do not encode it as a constant fill knob.

## Last scheduling cut: attach-as-ready

`RETRO_V4_ATTACH_AS_READY=1` (default): attach and expand each mol when its ScoreSlice returns, not when the rest of the tile finishes. HF generate is still one kernel. After this cut the bound job on this \(\mathcal{R}\) is the atomic 5015 POST. Further pipeline splits either change that quantum or only create \(\rho\).

## Pareto

Among feasible **landed** \(\theta\), keep the nondominated set under
maximize \(J\), minimize \(T\), and optionally maximize a quality metric.
Unlanded schedules belong on a dashed front, never as `b_star` to apply.
