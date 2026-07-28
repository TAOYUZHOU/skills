# Iteration Contract: Diff-Directed Adversarial Gate

schema_version: 2

intent:
  Upgrade `delivery-alignment-iteration` so high-risk executable or protocol
  diffs must pass a real, diff-directed adversarial Agent gate, and ensure HARP
  self-evolve consumes the same rule without changing the active AIRS runtime.

non_goals:
  - Start the biopharmaceutical paper reproduction workspace in this iteration.
  - Modify or resume the AIRS workspace.
  - Replace deterministic regression tests with Agent judgment.
  - Require a paid Agent turn for documentation-only or evidence-only diffs.

ssot:
  - path: skills/delivery-alignment-iteration/SKILL.md
    reason: Active iteration procedure.
  - path: skills/delivery-alignment-iteration/references/iteration_contract_schema.md
    reason: Durable contract schema.
  - path: /root/autodl-tmp/taoyuzhou/harness-auto-research/harp/runtime/adversarial_audit.py
    reason: Existing HARP real adversarial Agent implementation.
  - path: /root/autodl-tmp/taoyuzhou/harp-self-evolve-architecture-20260727/harp-runtime-workspace
    reason: Active self-evolve runtime facts; read-only for this iteration.

deliverables:
  - id: D1
    path: skills/delivery-alignment-iteration/SKILL.md
    description: Risk-triggered real adversarial Agent gate procedure.
  - id: D2
    path: skills/delivery-alignment-iteration/references/iteration_contract_schema.md
    description: Versioned gate fields and evidence requirements.
  - id: D3
    path: skills/delivery-alignment-iteration/scripts/check_delivery_contract.py
    description: Backward-compatible validation for new contracts.
  - id: D4
    path: docs/harp_iteration_handoff.md
    description: Current iteration handoff SSOT.

acceptance_criteria:
  - id: A1
    description: A high-risk diff cannot be called complete without a real Agent attack, deterministic oracle, and zero escaped generated attacks.
  - id: A2
    description: Documentation-only changes can skip the extra gate only with a recorded risk decision.
  - id: A3
    description: Existing legacy contracts remain checkable while new contracts declare the adversarial gate explicitly.
  - id: A4
    description: Self-evolve's next material iteration resolves the global required skill and therefore receives the new rule; AIRS remains untouched.
  - id: A5
    description: A real-provider atomic validation records prompt, raw output, parsed attack plan, and deterministic result.

verification:
  - id: V1
    command_or_check: Run skill quick validation and contract checker fixtures for legacy and new schemas.
  - id: V2
    command_or_check: Run a real diff-directed adversarial Agent against this candidate diff in an isolated evidence directory.
  - id: V3
    command_or_check: Inspect self-evolve skill suggestion resolution and active process paths without mutating AIRS.
  - id: V4
    command_or_check: Review git diff and handoff reconciliation.

traceability:
  - acceptance: A1
    deliverables: [D1, D2, D3]
    verification: [V1, V2]
  - acceptance: A2
    deliverables: [D1, D2]
    verification: [V1, V4]
  - acceptance: A3
    deliverables: [D2, D3]
    verification: [V1]
  - acceptance: A4
    deliverables: [D1, D4]
    verification: [V3]
  - acceptance: A5
    deliverables: [D4]
    verification: [V2, V4]

risks:
  - The active self-evolve provider turn was constructed before this skill revision; the new rule applies on the next freshly built material iteration boundary.
  - The paper appears to publish only the 33-row multiobjective dataset, not every thermal-stability campaign used in the article.

final_claims_allowed:
  - The iteration skill requires a real diff-directed adversarial Agent for high-risk changes after V1-V4 pass.
  - Self-evolve is wired to the same global skill for future material turns after V3 passes.
  - No claim that the biopharmaceutical study has already been reproduced or that wet-lab results can be recreated computationally.

handoff:
  path: docs/harp_iteration_handoff.md
  policy: Update after every material implementation or verification step.

sandbox:
  scope: One real adversarial Agent plans attacks from the candidate skill/checker diff.
  fixture: Isolated evidence directory containing base/head identity and bounded diff.
  invoke: Real Codex provider through the existing HARP provider adapter or Codex CLI.
  assert:
    - Raw response is non-empty and parseable.
    - Proposed attacks cite changed paths and define deterministic oracles.
    - Generated executable attacks and fixed regression corpus have zero escapes.
  record:
    - Prompt
    - Raw provider output
    - Parsed attack plan
    - Test results

adversarial_gate:
  risk: high
  decision: required
  reason: The change alters a mandatory delivery gate and its deterministic checker.
  base: 36699dd5d0a1dca6c97cfd6c13949d2b6e4e0c57
  candidate: 061cc52dbe42e373b0ce92e0a26108c4f0326156
  attack_scope:
    - skills/delivery-alignment-iteration/SKILL.md
    - skills/delivery-alignment-iteration/agents/openai.yaml
    - skills/delivery-alignment-iteration/references/iteration_contract_schema.md
    - skills/delivery-alignment-iteration/scripts/check_delivery_contract.py
    - tests/test_delivery_alignment_contract_checker.py
  evidence_dir: docs/evidence/diff_directed_adversarial_gate
