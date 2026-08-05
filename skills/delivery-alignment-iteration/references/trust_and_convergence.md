# Trust, Risk, and Finite Convergence

This reference is normative for every new delivery-alignment iteration. It
replaces open-ended claims such as "the proof tool is unattackable" or "no
reviewer can find another issue" with a finite, reviewable authorization
contract.

## Root axiom

Every proof chain terminates at an explicitly accepted, candidate-external,
version-pinned trusted computing base (TCB) and a threat model frozen before
candidate execution. The iteration proves conformance to that finite contract;
it does not prove absence of every unknown bug.

The candidate may produce evidence, tests, traces, manifests, and proposed
findings. Candidate bytes never authorize their own promotion and never receive
private signing material. A verifier, runner, key, or policy change is a
separate `gate_tool_upgrade` iteration reviewed under the previously accepted
TCB plus independent static review. Only after that upgrade is accepted may its
hash become a root anchor for a product candidate.

## Trust sequence

Use this total order. Freezing names bytes; review authorizes promotion.

| Stage | Action | Depends on | Review object |
| --- | --- | --- | --- |
| T0 | Plan Review accepts the contract, threat model, risk tier, budgets, and root anchor. | prior root anchor | static contract |
| T1 | Implement only. Do not test or build candidate bytes in the candidate tree. Diagnostics use a candidate-external scratch clone and stay outside the evidence tree. | T0 | none |
| T2 | Byte-copy only object-database contents into a newly initialized candidate-external bare store; never invoke or copy candidate Git config, hooks, refs, or alternates. Freeze base, candidate, tree, path set, contract hashes, and patch hash. | T1 | none |
| T2.5 | Review the exact static `base..candidate` patch, checker source, schemas, and frozen contract. Accepted reviews emit external receipts bound to those hashes; a rejection archives this freeze. | T2 | static bytes |
| T3 | A host-pinned verifier recomputes identity only from the trusted bare store and requires the tier's accepted T2.5 receipts before returning `authorize_execution`; the host signs that authorization binding. | T2.5 | none |
| T4 | The host-constrained runner executes only the gates selected by the risk tier and carries the signed T3 authorization digest as predecessor. | signed T3 receipt | none |
| T5 | The host signs post-execution evidence bound to the T3 predecessor, candidate, patch, verifier, gates, and acceptance results. | T4 | none |
| T6 | Independent reviewers examine dynamic receipts and findings for the required number of rounds. | T5 | dynamic evidence |
| T7 | Cutover or synchronization receives separate authorization. | T6 closure receipt | release action |

Invariants:

1. Freeze has no approval meaning. T2.5 or T6 rejection archives one frozen
   candidate and returns to T1/T2; it cannot make future freezing impossible.
2. Review objects do not overlap. T0/T2.5 review static bytes and contracts;
   T6 reviews receipts, traces, executions, and residual risk.
3. Candidate bytes have zero execution before T3. There is no diagnostic
   exception inside the candidate or evidence tree.
4. `root_trust` is the external verification key or verifier hash, base commit,
   and frozen contract hashes. No in-chain artifact may replace it.
5. Phase-neutral candidate handoff bytes freeze at T2. Mutable phase truth after
   T2 lives in a candidate-external durable phase ledger.
6. Candidate Git configuration, hooks, replacement refs, text conversion, and
   external diff drivers are never consulted by the authorizing verifier.
7. Closure requires a verified signed chain from the pre-execution ledger to
   T3 authorization and then to the T4/T5 evidence receipt. Recomputing static
   eligibility at closure does not substitute for that predecessor chain.

## Frozen threat model

T0 must enumerate and hash:

- protected assets;
- attacker capabilities that the current iteration will exercise;
- trusted components, including the exact external verifier;
- explicitly excluded capabilities;
- predeclared security properties with stable IDs; and
- accepted evidence formats and semantic validators.

After T2, changing any item creates a new contract/candidate. A concern outside
the frozen model is a `scope_expansion_proposal`, not a current blocker. The
only exception is a concrete emergency P0 that demonstrates an authority
boundary crossing and receives independent adjudication; that forces a human
checkpoint and a new frozen model rather than silently extending the old one.

## Finding admissibility and appeal

A finding can block the current candidate as P0/P1 only when it contains all of:

- `violated_predeclared_property`, naming a property in the frozen model;
- `attacker_capability`, naming an included capability;
- `exact_candidate_identity`;
- `deterministic_counterexample_or_static_proof`;
- `authority_boundary_crossed: true`;
- severity and bounded remediation scope.

Missing fields, hypothetical future attacks, or requirements outside the model
are provisional/P2 and enter the residual-risk register. They may seed the next
iteration but cannot expand the current review criteria.

The author may appeal a finding once. One adjudicator, distinct from both the
author and original reviewer, must either uphold it against the frozen criteria
or reject/downgrade it. `upheld` preserves the blocker, `rejected` removes the
reviewer's veto, and `downgraded` makes it a nonblocking residual risk. The
adjudicator cannot add criteria. A second appeal or a new criterion requires a
human checkpoint or a successor contract.

The exceptional out-of-model emergency-P0 path uses a strict adjudication
record with `adjudicator_id` and `decision`. That adjudicator must also differ
from both author and original reviewer. Missing or self-adjudicated emergency
records are invalid and cannot expand the frozen frontier.

Completeness is a mapping obligation, not a forced-diff obligation. Keep exact
Git `changed_paths` separate from declared `affected_dependencies`. Every item
in their union receives exactly one disposition:

- `changed_and_verified`;
- `unchanged_dependency_verified`; or
- `not_applicable_with_proof`.

A reviewer may reject a missing or false disposition. A reviewer may not demand
that an unchanged file appear in the patch merely to satisfy a path checklist.

## Risk tiers and gates

Classify by authority reachability and blast radius, not line count.

| Tier | Typical change | Required gates |
| --- | --- | --- |
| R0 | Non-authoritative prose, comments, static assets | static schema/diff checks |
| R1 | Local code with no control, provider, parser, security, or release authority | static checks, targeted regression, one independent review |
| R2 | Parser, provider, queue, reviewer, artifact, retry/recovery, or other bounded authority boundary | R1 plus atomic boundary, reachable combined/history replay, one adversarial review |
| R3 | Root of trust, state machine, cross-workspace recovery, release/cutover, or system-wide authority | external host TCB, full dynamic gates, and two consecutive independent adversarial rounds |

`combined_chain_if_reachable` and `historical_replay_if_reachable` may be marked
not applicable only with a deterministic unreachability proof. R0/R1 must not
pay R2/R3 gate cost unless a reachable authority boundary raises their tier.

### Product-invariant test-harness fast path

An explicit human authorization or frozen T0 contract may reuse prior T2.5/T6
reviews for a successor that fixes deterministic collateral in a non-shipping
test or fixture. Eligibility requires byte-identical product/runtime/scripts,
release configuration, gate selection, verifier, runner, and contract
semantics; an exact diff proving no removed or weakened assertion, timeout,
leak check, skip, xfail, or negative cell; and passing results for both the
previously failing node and its declared affected regression boundary. Record
the authorization, cause, diff, product-tree hashes, and before/after evidence
in the external ledger.

This is review reuse, not product authorization or a lower risk label. Any
shipping reachability, product-tree change, ambiguity, or gate weakening uses
the ordinary tier. The fast path cannot be used to accept changes to this skill,
its verifier, runner, schemas, receipt semantics, or signing path.

## Finite closure rule

The frozen candidate closes when and only when all of the following are true:

1. every predeclared acceptance criterion passes with bound evidence;
2. every tier-required gate passes or has an allowed deterministic N/A proof;
3. no confirmed, unresolved, in-model P0/P1 remains;
4. the tier-required number of consecutive independent review rounds over the
   same candidate and threat-model hash report no new confirmed blocker;
5. executable counterexamples have zero escapes within the frozen attack
   manifest—not across an unbounded universe of possible attacks;
6. completeness mappings cover every declared path/dependency;
7. provisional findings and open P2s are recorded as nonblocking residual risk;
8. no review, rejection, attack, work-time, or human-report budget is exceeded.

R0 requires zero adversarial clean rounds, R1/R2 require one, and R3 requires
two. After closure, ordinary new risks create a successor iteration. Reopen the
closed candidate only when concrete evidence invalidates a signed, predeclared
property; otherwise the closure receipt remains immutable.

## Budgets and periodic human checkpoints

Unless T0 explicitly chooses stricter values, use:

```yaml
max_candidate_rejections: 2
max_adversarial_rounds_per_candidate: 2
max_new_attacks_per_round: 8
max_active_engineering_hours_without_checkpoint: 4
human_report_every_candidate_reviews: 2
max_appeals_per_finding: 1
```

Budget exhaustion never converts failure into acceptance. It produces a durable
human checkpoint with exact candidate, evidence, findings, spent budget, and
choices: narrow the contract, accept residual risk, authorize a new budget, or
stop. The same checkpoint is required at the configured review interval even
when ownership remains healthy.

## External verifier and phase ledger

For a product candidate, the verifier executable must resolve outside the
candidate repository and match `trust.verifier_sha256`. It receives public
verification material only. Private signing happens in a separate host process
with a scrubbed environment; candidate subprocesses inherit neither the key nor
its path. Candidate-authored checkers are treated as evidence producers.

The candidate handoff contains immutable, phase-neutral intent, identities, and
operator instructions. T2+ phase state, reviewer decisions, budget use,
receipts, and closure status belong to a durable ledger outside the candidate.
The ledger is bound to candidate, threat-model, verifier, and contract hashes
and carries a detached Ed25519 attestation verified with the root-anchored
external public key. Updating it cannot mutate frozen candidate bytes. The host
signer keeps its private key and key path out of every candidate subprocess.

The runner also supplies a candidate-external bare Git object store and expected
verifier, root-anchor, contract, and (for a gate-tool upgrade) prior-verifier
hashes independently of candidate data. The verifier disables candidate Git
configuration, replacement objects, hooks, external diff, and text conversion.
The signed ledger carries the exact tier-required accepted T2.5 receipts; they
are a hard precondition for T3, not optional prose evidence. The host signs the
T3 authorization binding to the pre-execution ledger payload. The T4/T5 runner
receipt is separately signed and names the authorization payload digest as its
predecessor while binding the gate and acceptance result digests. Closure
rejects a missing, reordered, mismatched, or tampered chain. A new verifier
copied to an external path remains unaccepted until the host supplies its
separately accepted hash. Path placement is never approval evidence.

Use `scripts/check_iteration_convergence.py` to validate a schema-v3 contract
and its external phase ledger. The script is a policy evaluator; authorization
comes from running its pinned hash in the external TCB. A checker executed from
the candidate may provide diagnostic output but cannot issue a closure receipt.
