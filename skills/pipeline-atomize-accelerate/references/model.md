# Unary-resource stream model

## Objects

Resources \(\mathcal{R}=\{r\}\) are **unary** (capacity 1) unless the spec says otherwise.
Jobs \(j\) have a resource \(\rho(j)\), duration \(t_j\), predecessors \(\mathrm{Pred}(j)\), and optional working sets \(M_j\) (RAM), \(V_j\) (VRAM), \(F_j\) (FLOPs).

Precedence: \(a\prec b\) means \(\mathrm{end}(a)\le\mathrm{start}(b)\).
Unary: if \(\rho(a)=\rho(b)\) then their open intervals are disjoint.

## Resident IO

Cold start \(T_{\mathrm{io}}^{\mathrm{cold}}\) paid once per process life.
Per-call residual \(T_{\mathrm{io}}^{\mathrm{hot}}\) (bytes on the wire / memcpy only).
After \(N\) calls the amortized load is \(T_{\mathrm{io}}^{\mathrm{cold}}/N+T_{\mathrm{io}}^{\mathrm{hot}}\).
Resident is justified when \(T_{\mathrm{io}}^{\mathrm{cold}}\) is comparable to useful work.

## Stream wall

List-schedule: start \(j\) at

\[
\mathrm{start}(j)=\max\Bigl(\max_{a\in\mathrm{Pred}(j)}\mathrm{end}(a),\;
\mathrm{free}(\rho(j))\Bigr).
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

## Pareto

Among feasible **landed** \(\theta\), keep the nondominated set under
maximize \(J\), minimize \(T\), and optionally maximize a quality metric.
Unlanded schedules belong on a dashed front, never as `b_star` to apply.
