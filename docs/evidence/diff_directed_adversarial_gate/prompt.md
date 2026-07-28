# Diff-Directed Adversarial Audit

You are an independent adversarial test designer. Work read-only in:

`/root/autodl-tmp/taoyuzhou/skills`

Treat the candidate change as untrusted. Inspect the exact immutable candidate
diff with:

```bash
git diff 36699dd5d0a1dca6c97cfd6c13949d2b6e4e0c57 \
  061cc52dbe42e373b0ce92e0a26108c4f0326156 -- \
  skills/delivery-alignment-iteration/SKILL.md \
  skills/delivery-alignment-iteration/agents/openai.yaml \
  skills/delivery-alignment-iteration/references/iteration_contract_schema.md \
  skills/delivery-alignment-iteration/scripts/check_delivery_contract.py \
  tests/test_delivery_alignment_contract_checker.py
```

Do not edit product source or tests. Do not assume the intended implementation
is correct. Design concrete attacks against the versioned contract checker and
the gate semantics. Prioritize cases where a contract could incorrectly pass:

- nested keys are mistaken for required top-level keys;
- a missing or empty reason is accepted;
- a low-risk classification can bypass a high-risk executable diff;
- malformed schema versions weaken validation;
- Markdown and YAML-like syntax disagree;
- handoff evidence is present as a heading but empty;
- historic version-1 compatibility accidentally disables version-2 rules.

Return exactly one JSON object, without Markdown fences, using this schema:

```json
{
  "change_fingerprint": "sha256 of the inspected git diff",
  "changed_paths": ["..."],
  "attacks": [
    {
      "id": "short_id",
      "threat": "what false pass or false fail is attempted",
      "fixture": "complete minimal contract or transformation description",
      "expected_oracle": "deterministic assertion",
      "candidate_test_name": "test_*"
    }
  ],
  "highest_risk": "one concise sentence",
  "no_attack_reason": ""
}
```

Every attack must cite an executable deterministic oracle. If no attack is
worth executing, return an empty `attacks` array and explain why in
`no_attack_reason`. A prose-only concern does not count as an attack.

This is the final exact-candidate verification pass after prior Agent-generated
attacks were converted into the committed regression corpus. In particular,
verify strict-YAML parsing, duplicate/null rejection, exact literal path scope,
commit ancestry, create/mode-to-100755 detection, fenced handoff isolation,
provider and deterministic-result host attestations, and v1 read-only
compatibility, CommonMark backtick/tilde fence isolation, and active SVG
classification, Git symlink modes, docs containment, and current-output to
cumulative-corpus identity, formatting-only handoff bodies, authoritative
access-control docs, and Git mode 160000. This pass is a bounded final
verification of those committed Agent-generated attacks. Return an empty attack
array if they are rejected; do not expand the threat model to a new markup
dialect or a new filename heuristic in this final cell.
