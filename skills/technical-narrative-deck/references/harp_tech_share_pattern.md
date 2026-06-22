# HARP Tech-Share Narrative Pattern

This reference captures the writing pattern of `/root/autodl-tmp/taoyuzhou/report/harp_tech_share.html` so it can be reused for future architecture decks, human-readable truth-source documents, and postmortems.

## Core Writing Move

The deck does not start with modules. It starts with a historical pressure:

> If agents can now do trustworthy short steps, what infrastructure is needed to chain those steps into long, reviewable work?

That move makes the system feel necessary before the architecture appears. Reuse this shape:

1. Name the historical shift.
2. Explain the newly possible behavior.
3. Show the new failure modes introduced by longer loops.
4. Present the system as a control surface for those failure modes.

## Canonical Route

Use this route when creating a technical share:

| Position | Section job | Example shape |
| --- | --- | --- |
| 1 | Title | "X: a control plane for Y" |
| 2 | Warm-up history | from small/manual workflow to long-loop workflow |
| 3 | Short-step breakthrough | why the primitive now works |
| 4 | Analogy | numerical error bounds, control systems, compilers, CI, etc. |
| 5 | Talk route | a numbered map of the rest of the artifact |
| 6 | Project highlight | "X is not A; it is B" |
| 7 | Capability map | 3-5 things the system can honestly do |
| 8 | Domain generalization | same control plane, different domain-specific prompts/skills |
| 9 | Repository/data model | remove topology confusion early |
| 10 | System map | components and arrows |
| 11 | One loop | input -> role/action -> evidence -> review -> decision |
| 12 | Gates and safety | what blocks false success |
| 13 | Roles and skills | who decides vs who executes vs who specializes |
| 14 | Self-evolve / feedback | how failures become engine lessons |
| 15 | Failure modes | wrong-direction diligence, fake closure, stale state |
| 16 | Ecosystem | how peer systems or benchmarks ask related questions |
| 17 | Case evidence | real runs, figures, paths, metrics, corrections |
| 18 | Roadmap / Q&A | what remains hard and what needs human judgment |

## Slide Unit Template

Each slide-like section should have:

```text
Eyebrow: local frame, not the main claim
Headline: one sentence claim
Body: why the claim matters
Visual: map / table / metric / case figure / contrast
Footer: source, provenance, or takeaway
```

Examples of strong headline shapes:

- "X is a control plane, not a training framework"
- "One tick is one bounded research turn"
- "Reviewers are policy-selected gates, not just extra agent calls"
- "Long loops expose new failure modes"
- "This figure is not a ranking; it shows which ideas can be absorbed"

## Architecture Truth-Source Variant

When the artifact is a long-form HTML architecture document rather than a slide deck, keep the slide-like section logic but add durable reference features:

1. **Recent Update**: what changed and why readers should care.
2. **Design Goal**: the philosophical center, preferably by contrast.
3. **Truth Sources**: table of files, owners, readers, and caveats.
4. **Role Boundaries**: what each agent role owns and must not own.
5. **State Flow**: one bounded cycle.
6. **System Map**: readable ASCII or SVG diagram.
7. **Failure Modes**: how confusion appears in practice.
8. **Common Misreadings**: false interpretation -> correct interpretation.
9. **Maintenance Rule**: when this document must be updated.

## Visual Grammar

Use visuals to compress system understanding:

- stage strip: historical evolution from manual to harnessed workflow
- mechanism map: repositories, runtime, agents, gates, target artifacts
- loop diagram: one bounded turn
- gate stack: layered checks before stop
- role matrix: planner/reviewer/executor/runtime responsibilities
- case layout: figure on one side, evidence cards on the other
- metric strip: big numbers with short labels
- failure path diagram: global objective vs wrong-direction local helper chain

Avoid decorative diagrams. Every visual should answer a comprehension question.

## Evidence Discipline

The pattern is persuasive because it distinguishes:

- real native score vs progress record
- artifact presence vs scientific completion
- current blocker vs superseded historical failure
- runtime protocol state vs scientific truth
- honest missing authority vs automatable work

When possible, cite:

- exact paths
- commits
- generated figures
- benchmark names
- metric definitions
- review verdicts
- repaired bug evidence

## Tone

Use a clear, opinionated engineering voice:

- warm-up enough to orient the reader
- decisive claims
- honest limits
- concrete evidence
- no triumphal autonomy framing
- no vague "AI can do everything" language

Good sentence pattern:

> The value is not proving full autonomy. The value is putting reliable short-step agency into an honest, reviewable, rollbackable long loop.

## Checklist Before Finishing

- Does the artifact explain why the system exists before listing modules?
- Does it define the system by contrast?
- Does every diagram answer a real reader question?
- Are human-owned decisions separated from runtime-owned state?
- Are old failures, blockers, and stale state clearly distinguished from current truth?
- Is there at least one real evidence bundle?
- Does the final chapter help a future agent avoid repeating old misunderstandings?
