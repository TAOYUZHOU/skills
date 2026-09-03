---
name: write-technical-blog
description: Write or revise rigorous, readable technical blogs and standalone HTML explainers from code, experiments, papers, mathematical models, or an existing report. Use when the user asks for a 技术博客, theory-first engineering/scientific explainer, mathematical derivation, notation glossary, interpretation of model components, evidence-backed method narrative, or a polished HTML article that connects equations, implementation, figures, limitations, transferability, and primary references.
---

# Write Technical Blog

Turn technical work into an article a new reader can enter without sacrificing mathematical or empirical precision. Prefer a standalone HTML page with relative assets unless the user requests Markdown or another format.

## Workflow

1. Inspect the source artifacts: code, metrics, model parameters, figures, papers, and the current draft.
2. State the reader, central question, task boundary, current answer, and one-sentence thesis before outlining.
3. Build a symbol registry before writing equations. Give every symbol one meaning, type/shape, unit, and layer.
4. Build a causal timeline: for every major revision, name the failure or information gap that forced the next step.
5. Write the argument in the sequence below, separating the main decision path from optional technical branches.
6. Generate, search for, or reuse only visuals that answer a concrete reader question.
7. Validate claims against artifacts and primary sources.
8. Render and inspect the final artifact; fix layout, missing assets, illegible equations, and unsupported claims.

For detailed section patterns and review questions, read [references/content-patterns.md](references/content-patterns.md).

## Narrative spine

Use the smallest subset that tells the whole story, normally in this order:

1. **First-screen reader contract** — state the problem, intended output, task/evidence boundary, current answer, and the decision this work informs. A first-time technical reader should understand these without following links.
2. **Milestones and terminology** — show 3–6 headline numbers or status facts, each with denominator/unit/comparator, plus a compact glossary for project-specific names. Never use an unexplained acronym in a milestone card.
3. **Causal timeline** — summarize how the solution evolved as `observed problem → operation → evidence → reason for next step`. Do not present chronology as a changelog without causality.
4. **Mental model** — show the system as a small composition of mappings or transformations.
5. **Main evidence path** — keep the minimum mechanism, experiment, and result needed to support the current conclusion in the normal reading flow.
6. **Notation catch-up** — add a compact symbol table before the first dense derivation; also define each variable at first appearance.
7. **Mechanism and derivation** — distinguish semantic layers and derive the non-obvious mathematical bridges without jumps.
8. **Failure modes and applicability** — distinguish mathematical validity, data support, physical meaning, and decision validity.
9. **Optional research branches** — place historical variants, negative-result diagnosis, full derivations, engineering internals, and speculative extensions in linked sections or accessible `<details>` blocks. Summarize their consequence on the main line before branching.
10. **Reproduction and references** — provide the smallest reproducible command, output paths, visual provenance, and primary citations.

## First-screen acceptance test

The opening viewport must contain, or clearly begin, all of the following:

- a plain-language problem statement and the exact object being predicted, compared, or decided;
- what information is available and missing, including whether labels are measured, expert, weak, or model-generated;
- the current answer with its strongest quantitative support and its most decision-relevant limitation;
- milestone cards whose numbers have units, denominators, evaluation split, or comparator where needed;
- definitions for project-specific method names and acronyms used above the fold.

Do not open with history, architecture inventory, notation, or an abstract claim such as “we propose a framework.”

## Mathematical writing contract

- Introduce a quantity in words before or alongside its first formula.
- Define index sets separately: for example, reserve `c` for semantic classes and `k` for mixture components.
- State units and shapes when they disambiguate meaning.
- Expand overloaded objects into partitions before conditioning or marginalizing them.
- Show the bridge step readers usually miss: Bayes normalization, a Lagrange constraint, a covariance partition, a Schur complement, a change of variables, or a numerical quadrature rule.
- After each derivation, say what the formula does operationally for one new input.
- Tie theoretical symbols to stored columns, model fields, or functions when implementation artifacts exist.
- Never let a posterior probability stand in for density support, calibration, causal evidence, or human preference.

## Components and local behavior

When a model has components, experts, clusters, heads, or latent states, include a table that answers:

| Question | Required explanation |
|---|---|
| What is the component? | Statistical object, semantic class, mechanism, or implementation partition |
| How is it fitted? | Objective and sufficient statistics or gradients |
| When is it active? | Gate, responsibility, support region, or routing rule |
| What local information does it provide? | Bias, slope, conditional variance, mode, uncertainty, or failure branch |
| What must not be inferred? | No unsupported causal, mechanistic, or class interpretation |

If two mixture layers exist, explicitly contrast them. Do not let equal component counts imply equal semantics.

## Evidence and visualization rules

- Label axes with units and distinguish observed, predicted, calibrated, and latent quantities.
- Plot data density or applicability alongside posterior curves when tails or empty regions can mislead.
- Visually de-emphasize unsupported extrapolation and explain the support rule in the caption.
- Prefer one visual for one claim. Avoid decorative dashboards and duplicate metrics.
- Use relative image paths in the deliverable and verify every referenced file exists.
- Make captions interpretive: state what the reader should notice and what the plot does not prove.

### Visual storytelling ladder

Choose the lowest rung that materially reduces explanation cost:

1. **Data-derived figure:** metrics, distributions, residuals, examples, or an ablation timeline generated from the actual artifacts.
2. **Code-native explanatory diagram:** task boundary, pipeline, state transition, causal timeline, or before/after failure mechanism drawn as SVG/HTML/CSS so labels remain editable and searchable.
3. **Generated illustration:** use only for a conceptual analogy or cover visual; label it as an illustration and never let it imply empirical evidence.
4. **Externally sourced image:** use image/web search only when a real apparatus, material, historical object, or domain context cannot be explained better with a diagram. Prefer official, public-domain, or clearly licensed sources. Save an approved local copy when permitted; record creator, page URL, license, access date, and modifications in the caption or a visual-sources block. Never copy a search-result thumbnail or hotlink an unstable asset.

Every visual must answer a named question in the surrounding paragraph. Alt text describes the information conveyed, not merely the objects shown. Avoid decorative stock imagery, screenshots of text, and figures that repeat a nearby table.

### Slides and carousels

Use a slide strip or carousel only when readers must compare at least three sequential stages, model variants, or representative cases. It is an optional branch, not the sole carrier of a main result.

- no autoplay; provide previous/next controls, position text, keyboard navigation, and reduced-motion behavior;
- keep a visible static overview or `<noscript>` fallback so printing, PDF export, and disabled JavaScript preserve the argument;
- give every slide a claim-led title, one focal visual, a short interpretation, and provenance;
- do not hide the current conclusion or evidence boundary inside a carousel.

## HTML output

Start from [assets/technical-blog-template.html](assets/technical-blog-template.html) when no project-native design system exists. Copy it into the user's output directory and replace all `{{...}}` tokens. Preserve:

- responsive typography and tables;
- MathJax equations;
- semantic sections, figures, captions, and references;
- light/dark readability;
- a clear evidence-boundary callout.

Do not embed secrets, machine-specific paths, or internal data in a publishable page. Keep local artifact links outside the article or convert them to safe relative links.

## Quality gates

Run:

```bash
python scripts/validate_blog.py /absolute/path/to/blog.html --strict
```

Then render or open the page and inspect at desktop and narrow widths. The validator is structural, not visual: a passing result never replaces rendering or fact-checking.

Before delivery, confirm:

- the title and first screen state the actual thesis;
- the first screen defines the problem, task boundary, current answer, milestones, and specialist names;
- the timeline states why each major revision followed from the previous result;
- the main conclusion is readable without opening optional branches or operating a carousel;
- notation is defined at first use or in the nearby glossary;
- every headline claim has a figure, table, calculation, citation, or explicit inference label;
- posterior, density support, uncertainty, and semantic meaning are not conflated;
- equations use consistent units and symbols;
- limitations change how the output should be used, rather than serving as generic disclaimers;
- all figures load and all template tokens are removed;
- every external or generated visual is labeled and has appropriate provenance;
- references prefer original papers, official documentation, or first-party artifacts.
