status: partial
updated_at_utc: 2026-08-04T00:00:00Z
iteration: delivery-alignment-trust-convergence-v3-20260804
contract: docs/iteration_contracts/delivery_alignment_trust_convergence_v3_20260804.yaml
candidate: external-freeze-ledger

## Intent

Replace the open-ended candidate-authored proof loop with a finite,
risk-tiered, candidate-external authorization model.

## Non-goals

This candidate does not modify HARP runtime, r8, live workspaces, or a post-v19
successor, and it cannot authorize its own gate-tool upgrade.

## Current truth

The schema-v3 contract and trust/convergence reference define candidate-neutral
T0 policy. Exact candidate, tree, patch, actual path set, reviews, budgets, and
phase state are external signed T2+ facts and therefore do not create a commit
self-reference in this file.

## Candidate operating instructions

Resolve all current phase, reviewer, budget, rejection, and closure truth from
the external signed ledger identified by the contract. This candidate handoff
does not assert a mutable T-stage and cannot authorize promotion.

## Completed changes

- Added schema-v3 trust, threat-model, risk-tier, finding, appeal, budget,
  completeness, and finite closure rules.
- Added an external-ledger convergence evaluator with Ed25519 attestation.
- Bound freeze recomputation to a host-prepared bare Git store and made accepted
  T2.5 receipts a hard T3 precondition.
- Required finding reviewers and appeal adjudicators to remain independent of
  the candidate author, with the adjudicator also distinct from the reviewer.
- Demoted schema-v1/v2 CLI behavior to non-authorizing historical audit.
- Added directed tests for low-cost R0 closure, R3 review rounds, moving review
  criteria, real blockers, budget checkpoints, external verifier/ledger
  boundaries, malicious candidate Git configuration, missing static-review
  receipts, author self-adjudication, signature tamper, and completeness
  dispositions.

## Verification evidence

Development diagnostics showed skill quick validation and the directed test
modules passing. They are non-authorizing T1 observations. The exact frozen
candidate must be rerun only after T3 authorization; T4/T6 receipts belong in
the external phase ledger.

## Residual risks and authorization boundary

- A candidate-contained or merely externally copied verifier is diagnostic
  only. This gate-tool upgrade requires a host-supplied accepted verifier hash
  before it can become product promotion authority.
- OpenSSL 3.x remains a declared external dependency.

## Exact next action

Use the externally signed ledger to determine whether the frozen candidate is
rejected, ready for external acceptance, or accepted; never infer that phase
from these candidate bytes.

## Final claims allowed now

Only claims listed in the schema-v3 contract and authorized by an external
closure receipt are allowed. These bytes alone authorize no skill acceptance,
post-v19 launch, cutover, or live-runtime repair.
