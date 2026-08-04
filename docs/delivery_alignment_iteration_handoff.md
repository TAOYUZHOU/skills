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

## Current phase

Implementation and local directed diagnostics are complete under the prior
skill's gate-tool bootstrap rules. The next immutable candidate will enter T2,
followed by exact static and forward review. This phase statement is
informational and does not authorize promotion.

## Completed changes

- Added schema-v3 trust, threat-model, risk-tier, finding, appeal, budget,
  completeness, and finite closure rules.
- Added an external-ledger convergence evaluator with Ed25519 attestation.
- Demoted schema-v1/v2 CLI behavior to non-authorizing historical audit.
- Added directed tests for low-cost R0 closure, R3 review rounds, moving review
  criteria, real blockers, budget checkpoints, external verifier/ledger
  boundaries, signature tamper, and completeness dispositions.

## Verification evidence

Local diagnostics currently show skill quick validation and the new directed
test module passing. These are pre-freeze diagnostics, not T4/T6 authorization
receipts. Frozen-candidate results belong in the external phase ledger.

## Open blockers and risks

- The candidate has not yet been frozen or independently reviewed.
- The verifier hash in the contract must be reconciled after the final code edit.
- This gate-tool upgrade requires external acceptance before use as a product
  promotion authority.

## Exact next action

Freeze one commit containing only this iteration's files, compute its tree,
binary patch, contract/model/verifier hashes and path set, then obtain two
independent exact-diff reviews and sign the external phase ledger.

## Final claims allowed now

The implementation draft exists and local diagnostics pass. No claim of skill
acceptance, post-v19 launch, cutover, or live-runtime repair is currently
allowed.
