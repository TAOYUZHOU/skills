# HARP Iteration Handoff

status: complete
updated_at_utc: 2026-07-28T11:45:00Z
iteration: diff-directed-adversarial-gate
contract: docs/iteration_contracts/diff_directed_adversarial_gate.md

## Intent

Add a real, risk-triggered diff-directed adversarial Agent gate to the shared
iteration skill, prove it with deterministic and live-provider evidence, and
verify that self-evolve consumes the shared rule without touching AIRS.

## Non-goals

- Do not start the requested paper-reproduction workspace yet.
- Do not mutate, resume, or stop AIRS.
- Do not make Agent opinion replace deterministic test oracles.

## Current truth

- The shared iteration skill now requires a real diff-directed adversarial
  Agent for high-risk source, executable, protocol, schema, authority, or
  active-content changes.
- Self-evolve's canonical queue resolves this exact global skill with
  `mode=required`; it has no exemption at promotion or engine-sync boundaries.
- AIRS was not mutated, stopped, resumed, or used as a sandbox in this iteration.
- ACS/ETH publish the article and supporting information; the public structured
  dataset currently identified is a 33-row multiobjective XLSX.

## Current phase

Closed. The exact immutable candidate was re-audited by a real provider Agent;
the final Agent found no new escaping attack, and the cumulative attack corpus
passes deterministic oracles.

## Completed changes

- Created this stable handoff and the versioned iteration contract before source edits.
- Added the risk-triggered real Agent gate and explicit self-evolve promotion rule.
- Added strict, unique-key schema-v2 parsing for current contracts while keeping
  legacy v1 in a separate read-only compatibility path.
- Bound evidence to immutable base/candidate ancestry, literal changed paths,
  a canonical diff fingerprint, a real provider output, and externally keyed
  HMAC attestations for the provider receipt and deterministic gate result.
- Conservatively classified executable/source/schema/authority/config/package,
  executable-mode, symlink, gitlink, and active HTML/SVG changes as high risk.
- Made the Markdown handoff parser fence-aware and rejected empty,
  comment-only, and formatting-only evidence sections.
- Converted every valid adversarial finding into a named deterministic regression.

## Verification evidence

- Skill quick validation: passed.
- Final checker regression: `79 passed`.
- Full repository suite on candidate `061cc52dbe42e373b0ce92e0a26108c4f0326156`:
  `86 passed in 16.34s`.
- Exact candidate diff fingerprint:
  `47a3a5ab763c20f7eb0f5e31288a755dcb545296aa3c6d815dfd93188ccf62ec`.
- Final real Provider cell:
  thread `019fa882-4ada-7e62-8481-0e09af6f43e8`, non-empty parseable output,
  zero new attacks, return code 0.
- Self-evolve proof: canonical queue uses the global skill absolute path with
  `mode=required`; future fresh prompts receive the revised rule.
- AIRS proof: the contract explicitly excludes AIRS and no AIRS file or process
  was changed during this scoped iteration.

## Adversarial gate evidence

- Risk: high; this iteration changes an executable contract checker.
- Decision: a real diff-directed adversarial Agent is required.
- Prompt: `docs/evidence/diff_directed_adversarial_gate/prompt.md`.
- Cumulative parsed attack corpus: `agent_attack_manifest.json`.
- Exact final output: `final_agent_output.json`.
- Provider receipt: `live_provider_receipt.json`.
- Deterministic result: `gate_result.json`.
- Latest cumulative findings cover formatting-only handoff evidence,
  authoritative-document risk bypass, and gitlink mode bypass; all have named
  regression oracles.
- Result: 3 cumulative current-corpus attacks executed, 86 full tests passed,
  zero escaped attacks, and final exact-diff audit found zero new attacks.

## Open blockers and risks

- The HMAC evidence model protects against repository-only self-attestation; it
  does not claim protection from a malicious host administrator who controls
  both the repository and the external key.
- A provider turn already in flight cannot retroactively receive a revised
  skill prompt; the rule applies at the next fresh material iteration boundary.
- Full scientific reproduction requires unpublished observations and wet-lab
  assays that cannot be recreated from public files alone.

## Exact next action

If the user authorizes a computational-only reproduction scope, create an
isolated HARP workspace that acquires public data/code independently, records
provenance and licenses, and labels any unavailable wet-lab claim as unreproduced.

## Final claims allowed now

- High-risk iteration changes now require a real diff-directed adversarial
  Agent plus deterministic zero-escape evidence.
- Self-evolve is bound to the same shared iteration skill on fresh material turns.
- This iteration is complete; no claim is made that the biopharmaceutical study
  has already been reproduced or that wet-lab results are computationally available.
