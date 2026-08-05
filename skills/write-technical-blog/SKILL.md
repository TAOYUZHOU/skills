---
name: write-technical-blog
description: Write or revise rigorous, readable technical blogs and standalone HTML explainers from code, experiments, papers, mathematical models, or an existing report. Use when the user asks for a 技术博客, theory-first engineering/scientific explainer, mathematical derivation, notation glossary, interpretation of model components, evidence-backed method narrative, or a polished HTML article that connects equations, implementation, figures, limitations, transferability, and primary references.
---

# Write Technical Blog

Turn technical work into an article a new reader can enter without sacrificing mathematical or empirical precision. Prefer a standalone HTML page with relative assets unless the user requests Markdown or another format.

## Workflow

1. Inspect the source artifacts: code, metrics, model parameters, figures, papers, and the current draft.
2. State the reader, central question, evidence boundary, and one-sentence thesis before outlining.
3. Build a symbol registry before writing equations. Give every symbol one meaning, type/shape, unit, and layer.
4. Write the argument in the sequence below.
5. Generate or reuse only figures that answer a concrete question.
6. Validate claims against artifacts and primary sources.
7. Render and inspect the final artifact; fix layout, missing assets, illegible equations, and unsupported claims.

For detailed section patterns and review questions, read [references/content-patterns.md](references/content-patterns.md).

## Narrative spine

Use the smallest subset that tells the whole story, normally in this order:

1. **Answer and status** — say what was built, what it establishes, and whether the method is standard, adapted, or genuinely novel.
2. **Mental model** — show the system as a small composition of mappings or transformations.
3. **Notation catch-up** — add a compact symbol table near the first equation; also define each variable at first appearance.
4. **Mechanism by layers** — give each latent variable, model component, and output a distinct semantic role.
5. **Derivation without jumps** — move from assumptions to likelihood/objective, update or inference equations, then the deployed output.
6. **Concrete parameter interpretation** — translate fitted weights, means, variances, slopes, correlations, or gates into local behavior without inventing mechanisms.
7. **Evidence next to claims** — place each plot or table immediately after the paragraph it supports.
8. **Failure modes and applicability** — distinguish mathematical validity, data support, chemical/physical meaning, and decision validity.
9. **Transfer and alternatives** — identify what is invariant, what must be recalibrated, and what a more expressive method can and cannot solve.
10. **Reproduction and references** — provide the smallest reproducible command, output paths, and primary citations.

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
- notation is defined at first use or in the nearby glossary;
- every headline claim has a figure, table, calculation, citation, or explicit inference label;
- posterior, density support, uncertainty, and semantic meaning are not conflated;
- equations use consistent units and symbols;
- limitations change how the output should be used, rather than serving as generic disclaimers;
- all figures load and all template tokens are removed;
- references prefer original papers, official documentation, or first-party artifacts.
