# HARP Iteration Handoff

status: partial
updated_at_utc: 2026-08-01T05:33:42Z
iteration: delivery-alignment-combined-chain-replay
contract: docs/iteration_contracts/delivery_alignment_combined_chain_replay_20260801.yaml

## Intent

Require applicable high-risk iterations to verify the complete executor-to-health
lifecycle with one combined atomic chain and replace clean hand-authored HARP
workspace mocks with sanitized replays derived from three real workspace histories.

## Non-goals

- Do not repair or mutate the three live workspaces.
- Do not retain raw databases, prompts, scientific artifacts, credentials, or absolute paths.
- Do not replace focused unit, regression, one-hop atomic, clean-room, or exact-diff gates.
- Do not treat historical replay evidence as current live-state or completion authority.

## Current truth

- Canonical skill: `skills/delivery-alignment-iteration/SKILL.md`.
- Current immutable base: `d94d282c7982a6de7041343d12df9cee5cf8a7c1`.
- Rejected first candidate: `84f7ddeb2c7c1e8c14c9bbf48325f93754627485`; replacement pending freeze.
- Three read-only source histories exhibit distinct classes: accepted-review projection mismatch, blocked missing-artifact dependency, and partial-result materialization.
- The working tree already contains unrelated untracked evidence and skills; they are outside this iteration.

## Current phase

The first frozen candidate failed independent forward and exact-diff review.
All eight executable escapes plus the fixture-path mismatch are repaired and
covered by regression tests. A replacement candidate and clean Agent rerun are pending.

## Completed changes

- Read the complete `skill-creator` and `delivery-alignment-iteration` skills plus the applicable interface/schema references.
- Audited the three live histories without writing their queue, SQLite, cron, or workspace files.
- Defined bounded deliverables and explicit privacy/non-authority constraints for real-history replay.
- Added mandatory Combined Lifecycle Chain and Historical Replay gates to the skill, schema reference, and Agent-facing metadata.
- Added a read-only, double-read-stable, SQLite-query-only capture script and a fail-closed replay/receipt validator.
- Captured three pseudonymous control-shape profiles with no raw database, prompts, free-form output, scientific artifacts, credentials, or absolute source paths.
- Added checker enforcement for required versus deterministically unreachable gates and recomputed evidence validation.
- Added regression tests for missing declarations, evidence tampering, all three historical signatures, ordered chain stages, and manifest binding.
- Rejected candidate `84f7ddeb2c7c1e8c14c9bbf48325f93754627485` after independent review found a fixture-path mismatch and the real exact-diff Agent generated eight executable escapes.
- Repaired self-authored receipts, prose-only unreachability, risk self-downgrade, profile-field injection, stale event digests, source-directory output, torn multi-file snapshots, and absolute evidence paths.

## Verification evidence

- Pre-change repository HEAD is `d94d282c7982a6de7041343d12df9cee5cf8a7c1`.
- The three source workspaces were inspected read-only and no repair command was executed.
- `pytest -q tests/test_delivery_alignment_contract_checker.py tests/test_delivery_alignment_history_replay.py`: 96 passed after adversarial repairs.
- `pytest -q`: 103 passed after adversarial repairs.
- `quick_validate.py skills/delivery-alignment-iteration`: `Skill is valid!`.
- `validate_harp_chain_evidence.py` reports all three replay oracles and the combined receipt valid.
- Durable evidence: `docs/evidence/delivery_alignment_combined_chain_replay_20260801/`.
- `git diff --check`: passed before candidate freeze.

## Adversarial gate evidence

- Risk is high because this changes the canonical skill and checker behavior.
- Base is `d94d282c7982a6de7041343d12df9cee5cf8a7c1`.
- Rejected candidate `84f7dde` had a real Codex exact-diff turn with fingerprint `8c03a4094819a5746cff943aabfd44511e5a7ae552771bb3649f621de33226ce`; it returned eight current attacks, so the gate correctly failed.
- The earlier bubblewrap-blocked turn is retained as diagnostic evidence and is not counted as a gate.
- Replacement immutable candidate, clean independent output, zero-escape deterministic result, and final trusted attestations remain pending.

## Open blockers and risks

- A generic evidence validator cannot substitute for a target repository's real producer-to-consumer integration test.
- Existing unrelated untracked files must remain unstaged and unchanged.
- The durable combined receipt is explicitly skill-gate meta-validation; future HARP runtime changes must produce a target-local receipt from their real producers and consumers.

## Exact next action

Run an independent Agent forward test and exact-diff counterexample gate against
the replacement candidate after freezing the nine reviewed repairs.

## Final claims allowed now

- The iteration contract and partial handoff exist.
- The skill and checker now require additive combined-chain and real-history replay gates for applicable high-risk iterations.
- Three sanitized replay profiles reproduce the distinct observed failure signatures without claiming their live source workspaces are repaired.
- Deterministic implementation tests pass; immutable-candidate and adversarial-gate completion are not yet claimed.
