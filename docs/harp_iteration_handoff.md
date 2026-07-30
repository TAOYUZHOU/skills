# HARP Iteration Handoff

status: complete
updated_at_utc: 2026-07-30T04:38:00Z
iteration: repository-stewardship-gate
contract: docs/iteration_contracts/repository_stewardship_gate_20260730.yaml

## Intent

Extend the shared delivery-alignment iteration contract so a locally correct
change cannot silently worsen repository authority, footprint, evidence
retention, architectural concentration, quality debt, release purity, or
history safety. Clarify that adversarial review means happy-flow diffusion and
counterexample search, not a malicious-actor assumption.

## Non-goals

- Do not clean or restructure the HARP engine repository in this iteration.
- Do not delete evidence, migrate storage, rewrite history, or publish a release.
- Do not replace the completed Canonical Control-State Audit.
- Do not claim retroactive hot reload into an Agent prompt already in flight.

## Current truth

- `skills/delivery-alignment-iteration/SKILL.md` is the canonical shared copy.
- Its current pre-iteration content exactly matches immutable candidate
  `82c65660536f7032be95a5605b91f907c0002054`, including the completed Canonical
  Control-State Audit.
- HARP contracts reference this absolute canonical path, but this skill is not
  listed in the current Codex session's automatically discovered skill catalog.
- Explicitly reading the file applies it to this turn. A newly assembled turn
  that reads the path sees file updates; an already-issued prompt cannot be
  mutated retroactively.

## Current phase

The repository-stewardship and flow-diffusion gates are implemented. The first
immutable candidate `8657a41` passed static/full tests and the real-provider
skill-consumption cell, but exact-diff flow diffusion found three executable
overconstraint cases. Subsequent canonical-diff review found that the generic
escape still inherited HARP-shaped identity and writer fields. Candidate `6943549` now
binds identity, re-read/replay, readers, owner, frontier, and wakeup to the
project-declared mechanism; static/full tests, candidate-bound live provider,
final zero-counterexample review, signed receipts, and the current-schema
checker all pass.

## Completed changes

- Preserved the prior canonical-control-state candidate as the new iteration base.
- Created the schema-version-2 repository-stewardship iteration contract.
- Reconciled this stable handoff to the new current iteration.
- Added a repository-stewardship trigger to the workflow and skill description.
- Added separate footprint budgets, one-authority artifact rules, public versus
  forensic evidence tiers, responsibility-first module slicing, a quality-debt
  ratchet, clean-room release proof, and irreversible-history safeguards.
- Preserved the full Canonical Control-State Audit below the new gate.
- Synchronized `agents/openai.yaml` so the UI description and default prompt
  expose the new repository-stewardship gate.
- Clarified flow diffusion: start from expected flows, allow interacting
  dimensions, keep generalization concerns, and block only on executable
  deterministic counterexamples. No one-dimension restriction was added.
- Committed immutable local candidate
  `8657a41af5cfe43ed86c5fc97156e1c10c6963fd`; it has not been pushed.
- Real GPT-5.6 skill-consumption cell successfully read the complete skill and
  covered all seven stewardship categories; source hashes were unchanged.
- Exact-diff GPT-5.6 flow diffusion found three deterministic cases:
  HARP-specific supervisor architecture imposed on a generic SQL state machine,
  impossible provider gate for a provider-free reducer, and unsafe absolute
  migration-lane sunset.
- Replaced architecture mandates with project-declared semantic invariants,
  made real-provider proof conditional on a reachable Agent/provider boundary,
  and allowed one human-authorized bounded safety extension only when replay
  proves cutover would violate conservation.
- Committed repair candidate
  `a41a9c96d68524a356a3aae86d73c583a9cb30d7`; it has not been pushed.
- Canonical-diff review exposed one remaining atomic-SQL contradiction:
  workspace/contract/lineage/payload identity fields were still unconditional.
- Replaced that list with a project-declared injective typed identity profile;
  retained the full workspace/contract/entity/lineage/predecessor/payload tuple
  as the mandatory HARP profile.
- Committed current candidate
  `712fca4d3cfe135cff629c9256467c23686f6634`; it has not been pushed.
- Final canonical review caught and removed the last unconditional
  `single reducer writer` term; generic repositories now bind the single
  canonical transition writer or transaction mechanism, while HARP remains
  bound to its reducer writer.
- Committed final candidate
  `6943549bae2d5a565b5ed4ce2d94a40990dc7dff`; it has not been pushed.

## Verification evidence

- Pre-change comparison:
  `git diff --exit-code 82c65660536f7032be95a5605b91f907c0002054 --
  skills/delivery-alignment-iteration/SKILL.md` returned zero.
- No HARP engine file has been modified by this iteration.
- Skill validation:
  `quick_validate.py skills/delivery-alignment-iteration` returned
  `Skill is valid!`.
- Full skills-repository suite on repair candidate: `86 passed in 15.32s`.
- `git diff --check` passed.
- Exact candidate diff contains only
  `skills/delivery-alignment-iteration/SKILL.md` and
  `skills/delivery-alignment-iteration/agents/openai.yaml`.
- Skill length after the repair: 457 lines, within the skill-creator
  progressive-disclosure ceiling of 500 lines.
- Current-schema checker reports `schema_ok=true`, `handoff_ok=true`, and
  `diff_binding_ok=true`; final command returned `delivery contract OK`.
- Deterministic skill gate: 9/9 passed. Final full repository suite:
  86/86 passed.

## Adversarial gate evidence

- Risk: high because the target is an authoritative Agent behavior contract.
- Decision: required.
- Immutable base: `311c3e1e03a77132700acd03aa8f92de5bd1cb8a`.
- Immutable candidate: `6943549bae2d5a565b5ed4ce2d94a40990dc7dff`.
- Final Agent thread `019fb14b-3f41-72d0-aa42-04608e727653` returned zero
  executable counterexamples and three preserved generalization concerns.
- Candidate-bound skill-consumption thread
  `019fb14c-3510-7903-9751-85d8110eb980` passed 9/9 deterministic checks.
- Provider and deterministic gate receipts are separately HMAC-attested by the
  host key outside this repository.

## Open blockers and risks

- Automatic discovery still depends on installation or runtime prompt wiring;
  canonical-file modification alone cannot guarantee implicit loading.
- Generalization concerns remain deliberately non-blocking and retained in the
  final Agent output: indirect control-consumer inventory, verification cost at
  scale, heterogeneous transition semantics, publication authority, and skill
  loader completeness.

## Exact next action

Commit the bounded contract/handoff/public evidence bundle and push `main`
without force; verify remote identity from a clean fetch/export. Keep prior raw
attempt traces as untracked internal forensic evidence.

## Final claims allowed now

- The repository-stewardship gate is present in the canonical working copy and
  immutable candidate.
- Skill validation and all 86 repository tests pass.
- The prior Canonical Control-State Audit remains present.
- The final exact-diff Agent reports zero current executable counterexamples;
  all four cumulative counterexample families have deterministic regression
  coverage.
- The current-schema contract checker passes with separately host-attested
  provider and gate receipts.
- Newly assembled turns that explicitly read this canonical skill see the new
  rules.
- No automatic discovery, already-running prompt hot reload, HARP cleanup,
  adversarial-gate completion, history rewrite, or release is claimed.
