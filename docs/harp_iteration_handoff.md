# HARP Iteration Handoff

status: partial
updated_at_utc: 2026-08-01T08:50:00Z
iteration: delivery-alignment-combined-chain-replay
contract: docs/iteration_contracts/delivery_alignment_combined_chain_replay_20260801.yaml
candidate: 7d13ec84e5f2cdb581d4131b420e9a9f7fcb64ed

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
- Rejected first candidate: `84f7ddeb2c7c1e8c14c9bbf48325f93754627485`.
- Rejected second candidate: `ad783b17d84b55e31fc3655f16586521807de83c`.
- Rejected third candidate: `826c814ab0ece6cacac778089a219798220165ac`.
- Internally rejected fourth candidate: `27316c4b011d0663aeaeb9a046ed16536dac2e1c`.
- Rejected fifth candidate: `6ecd8409ac1c0dc4cdf52673fa45a3c7eeae12b4`.
- Rejected sixth candidate: `876153fc3dc8af5e6c2fa4723f4c9331ab1fb4af`.
- Rejected seventh candidate: `e606effd18de22e5da890fdea6bbbed1295e6c0b`;
- Rejected eighth candidate: `1269274d743d8ba47ee6b35bbdc6045500986d3b`;
- Rejected ninth candidate: `fb93b105d41cf81246065a312b4fd23e75a7df55`.
- Rejected tenth candidate: `ca0359e4d4128f97950c8be63825dbeadd742969`;
- Rejected eleventh candidate: `258047c1d4f5f0cbb4f8c7df0c7b15b4a22f7282`;
- Rejected twelfth candidate: `7d13ec84e5f2cdb581d4131b420e9a9f7fcb64ed`;
  thirteenth pending freeze.
- Three read-only source histories exhibit distinct classes: accepted-review projection mismatch, blocked missing-artifact dependency, and partial-result materialization.
- The working tree already contains unrelated untracked evidence and skills; they are outside this iteration.

## Current phase

The first frozen candidate failed independent forward and exact-diff review.
The third candidate's exact-diff review found one remaining command/test
semantic split. It was repaired and covered in fourth candidate `27316c4`.
Before sending the fourth candidate to the external Agent, internal review found that
argv membership alone could still be deselected. Constrained pytest plus parsed,
hash-bound JUnit evidence was implemented in fifth candidate `6ecd840`. Its
Agent review then correctly rejected using a metadata test as if it were a real
HARP runtime chain and identified the missing external-candidate CLI binding.
The sixth candidate's forward-bound review found replayable unreachability
attestation and a nested queue-count free-text channel; both are repaired.
The seventh candidate's exact-diff review found that a signed absence observation
could still be replayed into a different repository instance and that the handoff
candidate was not machine-bound. Both now fail closed through a current-root
declarative predicate and a contract/external/handoff three-way candidate check.
The eighth candidate's exact-diff review found an `output_assessment` nested
free-text escape, an author-selectable absence path that did not inventory the
repository, and a signed manifest without an independently bound capture
witness. The validator now closes the nested schema, the checker owns a fixed
repository-wide runtime-boundary inventory, and each real-history capture has a
separately host-attested receipt binding its tool and source/profile digests.
The ninth candidate's exact-diff review found that lifecycle signals could be
split across four modules and that a `missing` assessment could still claim
zero missing artifacts. Repository inventory now unions signals per package and
fails closed on code outside the skill-catalog layout; the blocked-artifact
oracle now requires positive missing count and `checked < expected`.
The tenth candidate's exact-diff review found that a required gate still
accepted meta-validation, that combined N/A could fall back to an arbitrary
absent path, and that lifecycle modules could split across evidence directories
or skill packages. Required receipts now demand the target-local boundary mode,
combined N/A accepts only the fixed inventory, and immutable-diff signals are
unioned repository-wide.
The eleventh candidate's exact-diff review showed that ten vacuous green tests
could still impersonate the chain and that immutable changed paths were scanned
from mutable worktree bytes. Target-local receipts now bind candidate-tree
producer/consumer file hashes plus per-test coverage contexts, while
applicability reads changed code directly from candidate Git blobs.
The twelfth candidate's exact-diff review showed that unrelated autouse calls
could satisfy file coverage, unchanged runtime files could be deleted only from
the worktree, and deleted lifecycle code was absent from candidate blobs. The
required chain now carries a same-run ordered causal digest trace; applicability
scans the complete candidate tree and base blobs for deletions.

## Completed changes

- Read the complete `skill-creator` and `delivery-alignment-iteration` skills plus the applicable interface/schema references.
- Audited the three live histories without writing their queue, SQLite, cron, or workspace files.
- Defined bounded deliverables and explicit privacy/non-authority constraints for real-history replay.
- Added mandatory Combined Lifecycle Chain and Historical Replay gates to the skill, schema reference, and Agent-facing metadata.
- Added a read-only, double-read-stable, SQLite-query-only capture script and a fail-closed replay/receipt validator.
- Captured three pseudonymous control-shape profiles with no raw database, prompts, free-form output, scientific artifacts, credentials, or absolute source paths.
- Added checker enforcement for required versus deterministically unreachable gates and recomputed evidence validation.
- Added regression tests for missing declarations, evidence tampering, all three historical signatures, ordered chain stages, and manifest binding.
- Added a trusted capture receipt and a fixed current-root runtime-boundary
  inventory; neither replay provenance nor chain applicability now depends on a
  candidate-authored path or unsigned capture claim.
- Required target-local receipts now bind one unique JUnit testcase to every
  lifecycle stage and reject nonzero aggregate suite counters; meta-validation
  remains explicitly diagnostic.
- Rejected candidate `84f7ddeb2c7c1e8c14c9bbf48325f93754627485` after independent review found a fixture-path mismatch and the real exact-diff Agent generated eight executable escapes.
- Repaired self-authored receipts, prose-only unreachability, risk self-downgrade, profile-field injection, stale event digests, source-directory output, torn multi-file snapshots, and absolute evidence paths.
- Rejected `ad783b1` and added manifest/unreachability host attestations, single-component path rejection, contract/candidate/test command binding, and per-stage producer/consumer/assertion bindings.
- Rejected `826c814` and required the attested invocation to include the bound chain test path as an exact argv token; ancestor/source output overlap is also rejected.
- Internally rejected `27316c4`; the command is now constrained to one pytest target plus JUnit, and the checker requires at least one testcase from that module with zero failures, errors, or skips.
- Rejected `6ecd840`; this skill-only iteration now records a host-attested combined-chain unreachability proof instead of claiming a runtime chain, while future HARP runtime targets remain required to execute it. High-risk checker runs also require the externally frozen candidate SHA.
- Rejected `876153f`; unreachability evidence now binds candidate/repository/cwd, and nested workflow/plan/enum maps are strict rather than free-form.

## Verification evidence

- Pre-change repository HEAD is `d94d282c7982a6de7041343d12df9cee5cf8a7c1`.
- The three source workspaces were inspected read-only and no repair command was executed.
- `pytest -q tests/test_delivery_alignment_contract_checker.py tests/test_delivery_alignment_history_replay.py`: 112 passed after the twelfth adversarial repairs.
- `pytest -q`: 119 passed after the twelfth adversarial repairs.
- `quick_validate.py skills/delivery-alignment-iteration`: `Skill is valid!`.
- `validate_harp_chain_evidence.py` reports all three replay oracles valid. The
  supplemental meta receipt validates only with the explicit diagnostic
  `--allow-meta-validation` flag and cannot satisfy a required runtime gate.
- Durable evidence: `docs/evidence/delivery_alignment_combined_chain_replay_20260801/`.
- `git diff --check`: passed before candidate freeze.

## Adversarial gate evidence

- Risk is high because this changes the canonical skill and checker behavior.
- Base is `d94d282c7982a6de7041343d12df9cee5cf8a7c1`.
- Rejected candidate `84f7dde` had a real Codex exact-diff turn with fingerprint `8c03a4094819a5746cff943aabfd44511e5a7ae552771bb3649f621de33226ce`; it returned eight current attacks, so the gate correctly failed.
- The earlier bubblewrap-blocked turn is retained as diagnostic evidence and is not counted as a gate.
- Candidate `ad783b1` produced six reported attacks; five were repaired. The sixth is the unavoidable fact that a Git commit cannot contain its own SHA and is handled by the post-freeze contract/handoff binding checked against the immutable commit.
- Candidate `826c814` produced one executable attack: a green sibling command could be attested while only hashing an unexecuted failing chain test. The argv-token binding repair closes it.
- Candidate `6ecd840` produced two executable attacks; both are repaired by the honest applicability decision and external candidate binding.
- Candidate `876153f` produced two executable attacks; both are repaired by candidate-bound unreachability evidence and nested-map sanitization.
- Candidate `e606eff` produced two executable attacks; both are repaired by
  current-root predicate re-evaluation and machine-bound handoff candidate metadata.
- Candidate `1269274` produced three executable attacks; they are repaired by
  strict nested assessment scalars, a fixed repository inventory predicate, and
  a separately attested capture witness.
- Candidate `fb93b10` produced two executable attacks; they are repaired by
  package-level signal union and the cross-field blocked-artifact invariant.
- Candidate `ca0359e` produced four executable attacks; they are repaired by
  target-local-only required receipts, the fixed combined-N/A predicate, and
  immutable-diff repository-wide signal union.
- Candidate `258047c` produced two executable attacks; they are repaired by
  immutable candidate-blob applicability and per-stage target-file coverage.
- Candidate `7d13ec8` produced three executable attacks; they are repaired by
  a same-run causal trace plus full candidate-tree and base-deletion inventory.
- Thirteenth immutable candidate, clean independent output, zero-escape
  deterministic result, and final trusted attestations remain pending.

## Open blockers and risks

- A generic evidence validator cannot substitute for a target repository's real producer-to-consumer integration test.
- Existing unrelated untracked files must remain unstaged and unchanged.
- The durable combined receipt is explicitly skill-gate meta-validation; future HARP runtime changes must produce a target-local receipt from their real producers and consumers.

## Exact next action

Freeze the thirteenth candidate, then rerun independent skill consumption plus
exact-diff counterexample review with its forward-binding patch.

## Final claims allowed now

- The iteration contract and partial handoff exist.
- The skill and checker now require additive combined-chain and real-history replay gates for applicable high-risk iterations.
- Three sanitized replay profiles reproduce the distinct observed failure signatures without claiming their live source workspaces are repaired.
- Deterministic implementation tests pass; immutable-candidate and adversarial-gate completion are not yet claimed.
