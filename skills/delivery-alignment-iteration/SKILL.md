---
name: delivery-alignment-iteration
description: Use when planning, implementing, reviewing, validating, converging, or handing off a project iteration where exact alignment between user intent, acceptance criteria, diff, tests, runtime evidence, review findings, handoff state, and final claims matters; especially for HARP runtime/recovery work, provider or queue boundaries, self-evolve, skills and proof-tool changes, historical workspace replay, releases, repository stewardship, or a prior "货不对板" delivery.
---

# Delivery Alignment Iteration

Use this skill to prevent implementation drift without creating an endless
proof loop. Its output is a finite, versioned contract and a candidate-external
phase ledger:

`intent -> acceptance -> frozen candidate -> tiered evidence -> finite review -> authorization`

## Non-negotiable trust rule

Every proof chain ends at an explicitly accepted, candidate-external,
version-pinned TCB and a threat model frozen before candidate execution. Prove
conformance to that finite contract; never claim that candidate-authored proof
tools are unattackable or that all possible future attacks have been exhausted.

Candidate checkers, tests, manifests, and traces are untrusted evidence
producers. They cannot authorize promotion and cannot receive private signing
material. The authorizing verifier is loaded from the installed skill or
another immutable host store outside the candidate repository and is bound by
hash. Updating that verifier is a separate `gate_tool_upgrade` iteration.

Read
[`references/trust_and_convergence.md`](references/trust_and_convergence.md)
before creating a new contract, assigning risk, reviewing a finding, declaring
closure, or changing this skill's proof tools.

## Mandatory workflow

1. Create a strict schema-v3 iteration contract before editing nontrivial
   files. Record exact intent, non-goals, SSOTs, deliverables, acceptance
   criteria, verification, traceability, residual risks, and allowed claims.
2. Create or locate one stable Markdown handoff under the target repository's
   `docs/` directory. For HARP, default to
   `docs/harp_iteration_handoff.md`. The candidate handoff is phase-neutral and
   freezes with candidate bytes. Store T2+ phase truth, review decisions,
   budgets, and closure in a durable ledger outside the candidate repository.
3. At T0 freeze the threat model, root anchor, risk tier, selected gates,
   finding criteria, appeal rule, budgets, and periodic human-report interval.
   Changing them after T2 requires a new contract/candidate.
4. Audit current truth before implementation. Run the Canonical Control-State
   Audit when behavior can alter an effective control outcome. Run the
   Repository Stewardship Gate when the diff can alter authority,
   reproducibility, release contents, storage, generated artifacts, or debt.
5. During T1 implement only. Do not test or build candidate bytes inside the
   candidate tree. If diagnostics are needed, use a candidate-external scratch
   clone and keep its outputs outside the evidence tree. For a mechanical
   multi-module change, use a persistent scratch clone with one-way sync from
   the candidate tree instead of a fresh clone per probe: the rule exists to
   keep build and test residue out of the candidate bytes, not to make the
   author's edit-verify loop expensive. Sync direction is candidate to scratch
   only; a scratch-to-candidate copy makes the frozen bytes unattributable.
6. At T2 the host byte-copies only Git object-database contents into a newly
   initialized candidate-external bare store; do not invoke candidate Git
   configuration or copy hooks, refs, config, or alternates. Then freeze
   immutable base, candidate, tree, exact changed-path set, exact binary patch
   digest, contract hashes, and threat-model hash. Freezing only names bytes;
   it is always allowed and carries no approval meaning.
7. At T2.5 independently review only static objects: the exact patch, contract,
   schemas, and any checker/runner source. Accepted reviews produce external
   hash-bound receipts; rejection archives that freeze and returns to T1/T2.
8. At T3 run the pinned external verifier over the host-prepared bare object
   store, root anchors, and the required accepted T2.5 receipts. It must return
   `authorize_execution`. Scrub private key material and key paths from every
   candidate subprocess. Candidate bytes have zero execution before this stage.
9. At T4/T5 run only the gates required by the risk tier. The host-signed
   runner receipt must name the T3 authorization payload as its predecessor and
   bind candidate, threat model, verifier, gate, acceptance, command, and
   evidence identities.
10. At T6 run the required independent review rounds. A P0/P1 blocks only when
    it satisfies the frozen finding-admissibility schema. Out-of-model concerns
    become `scope_expansion_proposal` or provisional/P2 residual risk unless an
    independently adjudicated emergency P0 forces a new human checkpoint.
11. Evaluate the finite closure formula with
    `scripts/check_iteration_convergence.py`. Budget exhaustion pauses for a
    human decision; it never converts failure into acceptance. Closure freezes
    the receipt. Ordinary later concerns seed a successor rather than reopening
    it; only concrete evidence invalidating a signed property may reopen it.
12. T7 cutover, branch synchronization, live mutation, deletion, publication,
    or release needs its own authorization after closure. Verification alone is
    not cutover permission.
13. Reconcile the handoff, external ledger, actual diff, and evidence before
    the final response. Claim only evidenced work and distinguish complete,
    partial, blocked, unverified, residual risk, and next action.

## Trust sequence and closure

Use the total order `T0 -> T1 -> T2 -> T2.5 -> T3 -> T4 -> T5 -> T6 -> T7`.
Static review never depends on future dynamic evidence, and dynamic review
never retroactively changes the static review object.

Closure requires all predeclared acceptance criteria, all tier-required gates,
no unresolved confirmed in-model P0/P1, the required consecutive clean review
rounds over the same candidate/model, zero escapes within the frozen attack
manifest, complete path/dependency dispositions, recorded P2/provisional risks,
and unexhausted budgets. R0 needs no adversarial round, R1/R2 need one, and R3
needs two. Do not substitute "keep reviewing until nobody imagines anything"
for this formula.

Default ceilings are **two consecutive no-progress candidate rejections**, two
adversarial rounds per candidate, eight new attacks per round, four active
engineering hours without a checkpoint, a human report every two candidate
reviews, and one appeal per finding. T0 may make them stricter, not looser,
without explicit human approval.

**Progress accounting (budget is consumed by stagnation, not by iteration).**
A successor that fixes at least one previously confirmed P1 semantic root
(machine-checked against the prior T2.5 `findings.json` and confirmed by the
next reviewer) does not consume the no-progress budget. A successor that fixes
no previously confirmed P1 consumes one no-progress unit; two consecutive such
units enter the durable human pause. A diminishing-returns trigger fires when
two consecutive candidates are rejected for defects in newly written
checker/verifier code rather than in product bytes: the runner must emit
`proof_tool_reuse_required`, and the next attempt must reuse an accepted
verifier-pool member instead of authoring a new proof tool. See
[`references/verifier_pool.md`](references/verifier_pool.md).

### Product-invariant test-harness fast path

Do not spend an independent review round on a locally discovered test-harness
defect when an explicit human authorization or the frozen T0 contract selects
this fast path and all of these conditions are machine-evidenced:

- the failure is deterministic in an already authorized gate;
- the successor changes only non-shipping tests or fixtures and external phase
  records; product, runtime, scripts, release configuration, gate selection,
  verifier, runner, and contract semantics are byte-identical;
- the delta only removes test collateral (for example shared-module mock
  leakage) and does not delete or weaken an assertion, timeout, leak check,
  skip, xfail, or negative cell; and
- the exact failed node plus its declared affected regression boundary pass,
  while reused gates remain bound to identical product-tree hashes.

The author records the deterministic cause, exact diff, product-tree identity,
targeted before/after result, affected regression result, and the human/T0
authorization in the external ledger. T2 still freezes the successor bytes,
but T2.5/T6 may reuse the previously accepted reviews without a new reviewer
for this delta. Any ambiguity, shipping-code reachability, gate weakening, or
product-tree change exits the fast path and follows the normal risk tier. This
exception cannot authorize a change to this skill or its proof tools; those
remain `gate_tool_upgrade` work.

### Verifier pool: reusable proof tools

Proof tools (checkers, runners, verifiers) are **pool members, not candidate
deliverables**. A candidate supplies data (contract, path list, commit
identities, expected digests); verification logic lives in versioned,
SHA-256-pinned verifiers installed outside the candidate repository. This is
what makes closure finite: each verifier is reviewed once at a high intensity
and then reused for every release.

Three layers, isolated by change frequency:

1. **Parameters** (changes every release; data, not code): base/candidate
   commits, path list, contract hash, expected tree and patch digests. A
   parameter change needs no verifier review.
2. **Domain adapters** (low frequency; declarations, not logic): HARP state
   schemas, authority maps, event-type inventories. A new event type or state
   object is a schema declaration change (light independent review), never a
   verifier edit.
3. **Kernel** (very low frequency; the only high-intensity-reviewed code):
   Git object-database integrity, TOCTOU-safe object reads (dirfd-relative,
   no checkout-path opens), digest and signature primitives. Kernel changes go
   through the full `gate_tool_upgrade` sequence with the complete historical
   fixture regression.

**Non-regression guarantee.** Every historically confirmed defect becomes a
frozen fixture (for example the v19 authority-root conflating candidate and
the TOCTOU/mutable-checkout split). Any verifier change must pass the full
fixture set before it can be pinned. See
[`references/verifier_pool.md`](references/verifier_pool.md).

**Product-defect fixtures are mandatory, not only proof-tool fixtures.** A
fixture set that covers verifier bugs while product defects live only in
candidate-authored `tests/` grounds regression protection in evidence this
skill itself declares untrusted. Every closure must contribute at least one
`reject_<incident>` fixture to the pool: a base-negative/candidate-positive
pair, stored outside the candidate repository, replayable by a pool member
without candidate code. A contract may declare
`convergence.product_fixture: not_applicable_with_proof` only with a
machine-checked argument that the defect has no deterministic oracle. Closure
that adds no fixture and claims none is not applicable is invalid, because the
next candidate can silently reintroduce the same defect class.

### Release fast path: publish without re-authoring proof tools

When a candidate is a release bootstrap or publication wrapper over bytes that
were already independently accepted (`release_kind: release_bootstrap` in the
contract) and the diff is packaging/governance-only with no runtime byte
change, the workflow shrinks to:

`T0 freeze contract -> T1 produce data (path list, digests) -> T2 freeze ->
T2.5 independent review of the DATA (path list and contract) -> T3 invoke the
accepted verifier-pool member with parameters -> T6 one reviewer on the verifier
receipt -> T7 human cutover approval.`

The review object collapses from proof-tool code to release data; dynamic
gates are skipped unless the tier derivation detects runtime-byte changes.
`git_integrity_verifier` in
[`references/verifier_pool.md`](references/verifier_pool.md) is the worked
example.

## Risk routing

Classify by reachable authority and blast radius, not by line count:

- R0: non-authoritative prose/comments/static assets. Run static checks.
- R1: local non-control code. Add targeted regression and one independent
  review.
- R2: parsers, providers, queues, review/artifact boundaries, retry/recovery,
  or another bounded authority edge. Add an atomic boundary cell, reachable
  combined/history replay, and one adversarial review.
- R3: root-of-trust, state-machine, cross-workspace recovery, release/cutover,
  or system-wide authority. Use the external host TCB, full dynamic gates, and
  two consecutive independent adversarial rounds.

`combined_chain_if_reachable` and `historical_replay_if_reachable` require a
machine-checked unreachability proof to be N/A. R0/R1 do not inherit the full R3
gate merely because the patch is executable.

### Tier derivation (automatic, not self-declared)

The risk tier is **derived by the runner from the exact changed-path set and an
authority map** (for example `harp/runtime/` provider/queue/checkpoint/state
paths trigger R3; `docs/` and `prompts/` trigger R0/R1). A contract may declare
`risk_profile.tier`, but the derived tier wins when it is higher; implementers
cannot lower their own tier. When the derived tier is R0/R1 and the changed
paths are packaging/governance-only over already accepted bytes, the runner
selects the release fast path above. Gate selection, budget ceilings, and the
required review count all come from the derived tier, not from prose.

**Reachability downgrade (shadow deliverables).** Path-derived tiers cannot
distinguish "rewrites the queue reducer" from "adds an observe-only module
under the same directory", so they price a root-cause refactor and a one-line
patch identically. A changed path set that a pool member proves
control-unreachable derives one tier lower, floor R2, when all of these hold
machine-checked: no control outcome, status, projection, event payload, or
admission decision can differ with the new code present; the new surface is
write-only into a diagnostic projection; and removing the new module leaves
behavior byte-identical on the tier's replay corpus. The proof is a pool-member
verdict over the exact patch, never an author declaration, and the downgrade is
recorded with the verdict digest. Absent that verdict the path-derived tier
stands. This preserves "implementers cannot lower their own tier" while making
staged refactors affordable.

**Root-cause credit.** An iteration that provably retires historical fixture
classes is not priced like a patch of the same blast radius. When a candidate
makes N >= 2 existing pool fixtures pass **by removing the mechanism they
exercise** rather than by adding a guard per fixture, the runner records
`root_cause_retirement: N` and raises the cost/value threshold and the active
engineering-hours ceiling by the T0-frozen credit factor (default N, cap 4x).
Gate selection, required review count, and adversarial rounds are unchanged:
credit buys budget, never assurance. A candidate that adds one guard per
fixture receives no credit, because sibling-path patching is the failure mode
this clause exists to make expensive relative to its alternative.

## Finding and completeness rules

A blocking P0/P1 must name the violated predeclared property, included attacker
capability, exact candidate, deterministic counterexample or static proof,
crossed authority boundary, severity, and bounded remediation scope. Otherwise
record it as provisional/P2. One adjudicator, distinct from both the candidate
author and original reviewer, may decide one appeal against the frozen criteria
and may not invent new criteria. The same identity separation is mandatory for
the exceptional out-of-model emergency-P0 adjudication path.

For every declared affected path/dependency, record exactly one disposition:
`changed_and_verified`, `unchanged_dependency_verified`, or
`not_applicable_with_proof`. Completeness does not require editing an unchanged
file merely to put it in the diff.

### Sibling call-site completeness

Path-level completeness does not catch the dominant recurrence pattern: a guard,
resolution rule, filter, or registration is corrected at one call site while
structurally identical siblings keep the defect, so the same root cause returns
as a "new" bug in an adjacent path. When a diff changes a guard condition, an
identity or anchor resolution, an input filter, a status-set membership test, or
a registration side effect, the runner must enumerate the sibling call sites:
the other callers of the same function, the other comparisons against the same
status-set literal, the other paths that must perform the same registration.
One disposition per sibling is then recorded using the vocabulary above. The
enumeration is mechanical (identifier and literal search over the candidate
tree) and its result is part of the evidence, not prose in a review.

An unenumerated sibling is an incomplete candidate, not a residual risk: it is
the specific thing that makes closure look clean while the defect class stays
open. `not_applicable_with_proof` remains available for a sibling whose context
genuinely differs, but the difference must be stated as a property, not as "not
in scope". Declaring the sibling out of scope in `non_goals` does not satisfy
this rule; a non-goal bounds what the candidate changes, never what the runner
must enumerate.

### Cost/value convergence clause

The closure formula is not purely logical; it also has an economic floor. At
each durable checkpoint the runner computes `spent_credits_or_hours` against a
value proxy (changed authority tier plus protected-asset weight). When the
ratio exceeds the T0-frozen threshold (default 10x, stricter permitted), the
runner must offer the human the choice between (a) continuing with an explicit
additional budget, or (b) **recording the unresolved items as non-blocking
residual risk and taking the release fast path**. Exhausted budget still never
converts failure into acceptance; this clause only changes the intensity of the
remaining proof, not its truthfulness. The threshold and the chosen branch are
recorded in the external phase ledger.

## Schema-v3 contract

Historical schema-v1/v2 contracts and `check_delivery_contract.py` remain
read-only compatibility artifacts. Do not use them to authorize a new
candidate. New iterations use strict YAML schema 3 and the external phase
ledger described in
[`references/iteration_contract_schema.md`](references/iteration_contract_schema.md).

Minimal shape:

```yaml
schema_version: 3
intent: "Observable iteration outcome."
non_goals: ["Explicit exclusions."]
ssot: [{path: "authoritative source", reason: "why"}]
deliverables: [{id: D1, path: "target", description: "result"}]
acceptance_criteria: [{id: A1, description: "observable condition"}]
verification: [{id: V1, command_or_check: "exact check"}]
traceability: [{acceptance: A1, deliverables: [D1], verification: [V1]}]
risks: ["Known residual risk."]
final_claims_allowed: ["Bounded claim after closure."]
release_kind: product_patch  # or release_bootstrap | tool_upgrade
handoff: {path: "docs/harp_iteration_handoff.md", policy: "phase neutral at T2"}
verifier_requirements: []  # fast path: [{id: git_integrity_verifier, version: v1, params: {...}}]
trust:
  verifier_origin: installed_skill
  verifier_version: trust-convergence-v1
  verifier_sha256: "<64 hex>"
  candidate_tool_role: untrusted_evidence_producer
  candidate_private_signing_material: forbidden
  bootstrap_mode: normal
  root_anchor:
    external_signing_public_key_sha256: "<64 hex>"
    base_commit: "<40 hex>"
    contract_hashes: ["<64 hex>"]
threat_model:
  frozen: true
  protected_assets: ["promotion authority"]
  attacker_capabilities: ["candidate controls repository bytes"]
  trusted_components: ["pinned external verifier"]
  excluded_capabilities: ["host key compromise"]
  security_properties: [{id: SP1, description: "candidate cannot self-authorize"}]
  evidence_formats: ["strict JSON receipt v1"]
risk_profile:
  tier: R3
  authority_reachability: true
  blast_radius: system
  rationale: "Changes promotion authority."
  changed_paths: ["path/to/file"]
  affected_dependencies: ["unchanged/path/whose contract is reverified"]
  adds_repair_surface: false   # true requires the unavoidability mechanism + removal condition
  reachability_downgrade:      # omit unless a pool member proved control-unreachability
    requested: false
    proof_verifier_id: ""
    proof_verdict_sha256: ""
  required_gates: [static, targeted_regression, atomic_boundary,
    combined_chain_if_reachable, historical_replay_if_reachable, host_tcb,
    independent_adversarial_1, independent_adversarial_2, full_dynamic]
review_policy:
  author_id: primary
  required_static_reviews: 2
  required_clean_rounds: 2
  max_appeals_per_finding: 1
  out_of_model_disposition: scope_expansion_proposal
  criteria_frozen: true
  reopen_rule: signed_property_invalidated
budgets:
  max_consecutive_no_progress_rejections: 2
  cost_value_threshold: 10
  root_cause_credit_cap: 4     # multiplier ceiling for root_cause_retirement credit
  max_adversarial_rounds_per_candidate: 2
  max_new_attacks_per_round: 8
  max_active_engineering_hours_without_checkpoint: 4
  human_report_every_candidate_reviews: 2
  max_appeals_per_finding: 1
convergence:
  acceptance_ids: [A1]
  completeness_required: true
  residual_risk_policy: record_nonblocking_p2_and_provisional
  requested_state: open
  product_fixture: {id: "reject_<incident>_<defect_class>", retires_classes: []}
  sibling_call_sites: [{site: "module.function:line", disposition: changed_and_verified}]
  root_cause_retirement: 0     # count of pool fixture classes retired by mechanism removal
phase_ledger: {mode: candidate_external, ledger_id: "stable-id"}
```

Run the pinned copy outside the candidate repository:

```bash
python3 /trusted/skills/delivery-alignment-iteration/scripts/check_iteration_convergence.py \
  --contract /path/to/iteration.yaml \
  --ledger /external/phase-ledger.json \
  --candidate-root /path/to/candidate \
  --trusted-git-dir /external/trust/candidate.git \
  --public-key /external/trust/ledger-ed25519-public.pem \
  --expected-verifier-sha256 <host-pinned-sha256> \
  --expected-root-anchor-sha256 <host-pinned-sha256> \
  --expected-contract-sha256 <host-pinned-sha256> \
  --expected-prior-verifier-sha256 <host-pinned-sha256-if-upgrade> \
  --phase pre_execution --json
```

Only after that invocation returns `authorize_execution` may T4 run candidate
bytes. Re-run the same pinned verifier with `--phase closure` after T5/T6; for a
gate-tool upgrade, also supply the independently accepted verifier hash:

```bash
python3 /trusted/skills/delivery-alignment-iteration/scripts/check_iteration_convergence.py \
  --contract /path/to/iteration.yaml \
  --ledger /external/phase-ledger.json \
  --candidate-root /path/to/candidate \
  --trusted-git-dir /external/trust/candidate.git \
  --public-key /external/trust/ledger-ed25519-public.pem \
  --expected-verifier-sha256 <host-pinned-sha256> \
  --expected-root-anchor-sha256 <host-pinned-sha256> \
  --expected-contract-sha256 <host-pinned-sha256> \
  --expected-prior-verifier-sha256 <host-pinned-sha256-if-upgrade> \
  --phase closure \
  --require-close --json
```

## Handoff and ledger

The stable handoff records intent, non-goals, frozen identities, current
evidenced truth, completed changes, verification, residual risk, allowed claims,
and exact next action. It is not an append-only event log and cannot claim a fix
before mapped verification passes.

The Ed25519-signed external phase ledger records the T2 candidate commit, tree,
patch digest, actual path set, accepted T2.5 static-review receipts, reviewer
IDs and rounds, findings and appeals, gate receipts, acceptance results,
completeness dispositions, residual risks, budget use, checkpoints, and
closure. It binds exact candidate, model, verifier, contract, and evidence
hashes. Its public key is hash-bound in the root anchor;
the signing key and its path never enter a candidate subprocess. The signed T3
authorization receipt binds the pre-execution ledger payload; the signed T4/T5
runner receipt binds that authorization as predecessor plus the gate and
acceptance result digests. Closure without this monotonic chain is invalid.
T2+ updates to this ledger must never alter candidate bytes.

For a gate-tool upgrade, copying the new verifier outside the candidate does
not constitute acceptance. Until the host supplies the independently accepted
new verifier hash, the only successful outcome is
`ready_for_external_acceptance`; only a later invocation with that host value
may return `close`.

## Diff-directed adversarial gate

Use adversarial review to seek deterministic counterexamples inside the frozen
threat model. Freeze exact diff and adjacent contracts; isolate reviewers from
the intended answer; let them write tests/repros/evidence but not product source;
prove base-negative/candidate-positive behavior when safe; and run the frozen
attack corpus plus regressions. "Zero escapes" means zero escapes in that
manifest. A prose concern without a deterministic oracle is provisional review
input.

Keep prompt, raw output, manifest, commands, exit codes, and hashes. A successful
provider turn is not a passing deterministic gate. Provider/runner receipts are
signed outside the candidate; verification uses only public material.

## Atomic boundary verification

For R2/R3 provider, prompt, role, parser, queue, or handoff changes, exercise the
smallest real changed slice and record input, raw output, parsed result,
downstream fact, and deterministic assertion. A provider-free path uses its real
boundary plus a machine-checked provider-unreachability proof. Broad regression
or benchmark runs do not replace this cell.

## Canonical control-state audit

When a change can alter state, identity, ownership, wakeup, admission, retry,
resume, completion, or migration, enumerate the canonical writer/transaction,
typed identity, predecessor revision, allowed events, authority, every reader
and projection, crash/replay semantics, and legacy authority paths removed.
Require one unique result under duplicate, stale, concurrent, partial-write,
owner-loss, and restart sequences that are reachable. Noncanonical inputs held
against fixed canonical facts must not change control truth. Use a bounded model
explorer and deterministic unreachability proofs for excluded sequences.

**The model explorer is a pool member, not prose.** Enumerating those sequences
by hand degrades to "we considered concurrency" instead of "we enumerated it".
The explorer is a versioned, SHA-256-pinned pool member (`state_machine_explorer`
in [`references/verifier_pool.md`](references/verifier_pool.md)) whose input is a
declared transition table at the domain-adapter layer: for each entity, the
status set, the status classes, and the legal `(status, event) -> status` cells.
Adding an entity or a status is an adapter declaration under light independent
review, never an explorer edit. The explorer must report a totality verdict (no
undefined cell reachable from an initial status) and a unique-result verdict
over the reachable duplicate/stale/concurrent/partial-write/owner-loss/restart
product. A transition table that no explorer consumes is documentation, and
this audit is not satisfied by it.

**Bounded holds.** Every wait state (awaiting review, obligation transferred to
a successor, nothing-changed suppression, admitted-without-outcome) must carry
`held_since`, a `deadline`, and a typed `on_timeout` disposition (escalate,
release, or human pause). Absence of an awaited event is then a typed timeout
event, never a resting state. A hold field that can be constructed without a
deadline is a finding: it makes permanent freeze representable, and permanent
freeze is indistinguishable from correct waiting in every projection. Latches
are subject to the same rule from the other direction: a one-shot boolean
(`escalated: true`) that gates recovery must instead carry an occurrence count,
last-occurrence time, and cooldown, so re-arming is expressible by construction
rather than added later per latch.

For HARP, the authority is the typed-event supervisor transaction and canonical
reducer. Provider prose or availability cannot decide deterministic transition
truth. Missing reconciliation ownership preserves the entity and enters a typed
human pause with a durable wakeup; it must not silently strand or terminate it.
Status-set membership is a property of the declared taxonomy; a diff that
introduces a new hardcoded status-set literal where a taxonomy predicate exists
is a finding under sibling call-site completeness above.

## Repository stewardship gate

When applicable, measure source, generated checkout, dependencies, evidence,
duplicates, and Git growth separately; preserve one authority per artifact;
tier public versus forensic evidence; avoid new architectural concentration;
ratchet touched-boundary quality without requiring unrelated rewrites; build
releases from a clean tree; and require explicit human approval, backup,
rollback, and exact targets for irreversible history/storage operations.

## Combined lifecycle and historical replay

For reachable HARP queue/handoff/review/artifact/completion/recovery/health
changes, use a target-local end-to-end test through real producers and consumers,
plus sanitized read-only replay of the three baseline archetypes and every
distinct causal signature from the motivating incident. One-hop mocks and
direct terminal-state construction do not close the gate. Preserve transport
versus semantic truth, exact provider identity, CAS/lease ownership, retry and
resume conservation, graph/admission convergence, artifact/reviewer manifest
binding, and a healthy happy path.

Follow
[`references/harp_combined_chain_replay.md`](references/harp_combined_chain_replay.md)
for stages, fixtures, oracles, and receipts. Its verifier is external under
schema v3; candidate-origin verification language applies only to archived v2
evidence.

## Self-evolve and proof-tool upgrades

Self-evolve is not exempt. A normal self-evolve product candidate uses this
skill and an already accepted external verifier. A change to this skill,
checker, validator, runner, receipt semantics, or signing path is a separate R3
`gate_tool_upgrade`: the prior TCB checks what it understands, at least two
independent reviewers inspect the exact new static bytes, forward tests exercise
the new policy, and the new verifier reports `ready_for_external_acceptance`
until a human accepts its hash. Never let the new checker close its own upgrade.

## Alignment rules

- User intent and current truth sources are constraints, not inspiration.
- A fallback is not delivery unless the contract accepts it.
- Prefer deletion, convergence, merge, downgrade, or deprecation before adding
  roles, states, repair lanes, compatibility paths, or new authorities.
- A plan is not a fix; a green test is not proof of an untested boundary.
- Runtime protocol, provider/environment, scientific, and release blockers stay
  distinct.
- If tests cannot run, record why, what remains unverified, and the exact next
  action.
- Final response and mutable phase ledger do not substitute for the stable
  handoff; none may claim more than the bound evidence.

### Repair-surface accounting (machine-checked)

The preference for deletion over new repair lanes is unenforceable as prose: a
subsystem can accumulate dozens of reconcilers, each individually justified by
an incident, until the repair surface is the architecture. The runner therefore
counts the repair surface on both sides of the diff (reconcile/repair/recover
entry points, compatibility branches, fallback paths, and status-set literals)
and records `repair_surface_delta`. A positive delta requires the contract to
declare `adds_repair_surface: true` with the mechanism that made the repair
unavoidable and the condition under which it can later be removed. A candidate
that adds a repair lane whose function is to compensate for a missing invariant
records the invariant as a P2 with a named successor, so the debt is visible
instead of dissolving into "fixed".

Two consecutive candidates in one subsystem with positive `repair_surface_delta`
and no retired fixture class fire the same diminishing-returns signal as
proof-tool churn: the runner emits `invariant_work_required`, and the next
candidate in that subsystem must either retire a fixture class or carry an
explicit human authorization to patch again.

## Parallelism (subagents)

When a tick contains independent read, audit, or draft subtasks, prefer bounded
parallel subagents over serial tool calls: each subagent works in a small
context and returns a summary, so the main agent's context stops growing
linearly with every probe. Subagent output is untrusted evidence: it enters the
evidence chain only after the main agent or the tier-required reviewer
verifies it. Subagents never hold signing material, promotion authority, or
verifier custody. Parallelism never relaxes the T-stage order, budget rules, or
any non-progress accounting.

## References

Read `references/iteration_contract_schema.md` for the complete schema and
ledger formats, `references/trust_and_convergence.md` for trust and finite
closure, and `references/harp_combined_chain_replay.md` whenever a HARP control
lifecycle or historical workspace fixture is reachable.
