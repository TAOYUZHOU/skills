---
name: technical-narrative-deck
description: Use this skill when writing technical sharing decks, architecture truth-source documents, engineering postmortems, project explainers, or human-readable system narratives that must align humans and agents on why a system exists, how it works, what evidence supports it, and where the honest boundaries are. Trigger for requests mentioning tech share, architecture docs, slides, narrative report, human-readable truth source, postmortem, roadmap, system explanation, or turning dense engineering history into a clear presentation.
---

# Technical Narrative Deck

Use this skill to turn dense engineering work into a clear, human-readable technical narrative. The target can be an HTML deck, a long-form architecture document, a markdown report, or a slide outline.

The style is based on a HARP tech-share pattern: start from the historical pressure that made the system necessary, define the mental model, show the mechanism, prove it with real cases, name failure modes honestly, and end with the design lessons.

## Quick workflow

1. Identify the audience and the job of the artifact:
   - leadership overview, engineering onboarding, architecture truth source, postmortem, roadmap, or live tech share.
2. Extract the core thesis:
   - "This system is not X; it is Y."
   - "The important problem is not A; it is B."
   - "The value is not autonomy theater; it is auditable, bounded progress."
3. Build the narrative route before writing sections:
   - why now
   - what changed historically
   - what the system is
   - how it works
   - what can go wrong
   - what evidence proves the point
   - what to do next
4. Write each section as a slide-like unit:
   - eyebrow: local context
   - headline: one claim
   - body: explanation or evidence
   - visual: map, flow, metric, table, case figure, or contrast
   - footer/source: provenance or takeaway
5. Keep the boundary between evidence and interpretation explicit.

## When writing an architecture truth source

Make the document useful to both humans and future agents:

- Put a "Recent Update" section near the top.
- Include a compact "What this document is for" statement.
- Name the source-of-truth hierarchy.
- Draw the system map.
- Explain data/state flow in one bounded loop.
- Add "common misunderstandings and correct readings."
- End with maintenance rules: when this doc must be updated.

## Narrative pattern

Prefer this sequence:

1. **Warm-up / history**: show the trend that created the problem.
2. **Thesis**: make a strong judgment in plain language.
3. **Mental model**: define the system by contrast.
4. **Capability map**: what it can actually do.
5. **Mechanism map**: components and arrows.
6. **Loop**: one cycle from input to evidence to decision.
7. **Gates / safety**: what prevents false completion.
8. **Roles / skills / interfaces**: who acts and how specialization enters.
9. **Failure modes**: where the system drifts or lies to itself.
10. **Ecosystem / benchmarks**: how the broader field frames the same problem.
11. **Cases**: concrete evidence bundles, not anecdotes.
12. **Roadmap / Q&A**: what remains uncertain and where human judgment still matters.

## Style rules

- Use strong, declarative section titles. Avoid vague labels like "Overview" when a claim is possible.
- Make each major section answer one question the reader actually has.
- Do not bury the main point under implementation details.
- Use comparisons to remove confusion: "control plane, not training framework"; "queue done, not scientific completion"; "mission graph, not raw history store."
- Include enough negative space in the argument: what the system does not solve, what remains human-owned, and what evidence is missing.
- Prefer real artifact names, paths, commits, metrics, and screenshots over generic claims.
- In Chinese artifacts, keep key system terms in English when they are code names or runtime concepts.

## References

For the extracted narrative pattern, read `references/harp_tech_share_pattern.md` before writing a substantial deck or architecture document.

For a direct HARP-tech-share-style writing scaffold with slide-by-slide fill-in templates and reusable HTML section snippets, read `references/harp_tech_share_writing_template.md`.
