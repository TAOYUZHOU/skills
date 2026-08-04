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
   clone and keep its outputs outside the evidence tree.
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
9. At T4/T5 run only the gates required by the risk tier, then bind receipts to
   candidate, threat model, verifier, commands, and evidence identities.
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

Default ceilings are two candidate rejections, two adversarial rounds per
candidate, eight new attacks per round, four active engineering hours without a
checkpoint, a human report every two candidate reviews, and one appeal per
finding. T0 may make them stricter, not looser, without explicit human approval.

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

## Finding and completeness rules

A blocking P0/P1 must name the violated predeclared property, included attacker
capability, exact candidate, deterministic counterexample or static proof,
crossed authority boundary, severity, and bounded remediation scope. Otherwise
record it as provisional/P2. One adjudicator, distinct from both the candidate
author and original reviewer, may decide one appeal against the frozen criteria
and may not invent new criteria.

For every declared affected path/dependency, record exactly one disposition:
`changed_and_verified`, `unchanged_dependency_verified`, or
`not_applicable_with_proof`. Completeness does not require editing an unchanged
file merely to put it in the diff.

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
handoff: {path: "docs/harp_iteration_handoff.md", policy: "phase neutral at T2"}
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
  max_candidate_rejections: 2
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
the signing key and its path never enter a candidate subprocess. T2+ updates to
this ledger must never alter candidate bytes.

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

For HARP, the authority is the typed-event supervisor transaction and canonical
reducer. Provider prose or availability cannot decide deterministic transition
truth. Missing reconciliation ownership preserves the entity and enters a typed
human pause with a durable wakeup; it must not silently strand or terminate it.

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

## References

Read `references/iteration_contract_schema.md` for the complete schema and
ledger formats, `references/trust_and_convergence.md` for trust and finite
closure, and `references/harp_combined_chain_replay.md` whenever a HARP control
lifecycle or historical workspace fixture is reachable.
