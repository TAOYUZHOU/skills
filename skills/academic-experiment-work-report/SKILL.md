---
name: academic-experiment-work-report
description: Use when turning ML, chemistry, bioinformatics, or other scientific experiment matrices into a high-quality Chinese work report, especially when results need Markdown, HTML, or PDF deliverables with figures, split-domain metrics, scientific model data diagnostics, data-cleaning provenance, queue/progress status, caveats, and next-step plans. For ML/scientific model reports, first use scientific-model-data-diagnostics when prediction and metadata artifacts are available.
metadata:
  short-description: Build rigorous Chinese Markdown/HTML/PDF reports for scientific experiment matrices
---

# Academic Experiment Work Report

Use this skill to turn a scientific experiment run into a work-report artifact that is honest enough for technical review and polished enough for project updates.

## Core Contract

The report must separate evidence from interpretation.

- State the evidence scope near the top: completed jobs, seeds, splits, model families, and pending matrix cells.
- Permanently split evaluation domains when the task has domain splits. Do not let mixed test metrics be the main conclusion.
- For ML/scientific model reports, run or incorporate `scientific-model-data-diagnostics` before writing final conclusions whenever prediction and metadata artifacts are available.
- Put the main answers first, then figures, then detailed tables, diagnostics, data cleaning, progress, caveats, and next-step plan.
- Use static PNG figures and relative paths in Markdown/HTML so the report can be archived and exported.
- Name missing experiments plainly. Do not describe pending work as completed.

## Mandatory Scientific Model Data Diagnostics Gate

For ML, chemistry, bioinformatics, materials, reinforcement learning, or domain-transfer reports, the report is incomplete unless it either includes `scientific-model-data-diagnostics` output or explicitly states why diagnostics could not be run.

Minimum required diagnostic content:

- Metric reliability by split/domain: n, R2/MAE/RMSE for regression; positive count, positive rate, confusion matrix/F1 for classification; return/reward and action/environment coverage for RL or policy tasks.
- Residual bias and largest residual patterns.
- Data-generating context strata when present, such as protocol, environment, source, instrument/simulator, cohort/site, measurement setting, action context, or missingness.
- Representation/novelty strata when present, such as cluster/family, nearest-neighbor distance, embedding distance, retrieval/similarity score, mechanism group, density, or extrapolation distance.
- A plain-language interpretation of whether model ranking is robust, fragile, or mostly explained by data/split structure.

If diagnostics reveal that a headline metric is fragile, the report must downgrade the claim and make the data issue visible in the conclusion section.

## Required Sections

1. **结论先行**
   - Answer the user's actual scientific questions.
   - Include quantitative values and the evidence boundary.
2. **固定汇报规范**
   - Define what must always be split, such as A-test/B-test/C-test, source groups, seeds, or domains.
   - Explain why mixed metrics are secondary.
3. **本轮实验矩阵目标**
   - Explain what the matrix is designed to decide: top architecture, fixed hyperparameters, data-volume effect, data noise, template/module validity, or calibration value.
4. **关键图表**
   - Include trend plots, scatter plots, confusion matrices, PR/ROC curves, or domain diagnostics as appropriate.
5. **分项结果表**
   - Report per-domain metrics, model family, setting, seed, and selection rule.
6. **Domain-Aware Diagnostics**
   - For OOD/domain failures, stratify by available source/domain fields.
   - Prefer source, scaffold/cluster novelty, fingerprint similarity quantile, template family, label range, pH/protocol, size bins, and residual direction.
   - For ML reports, this section should be populated from `scientific-model-data-diagnostics` outputs when possible.
7. **数据清洗策略**
   - Source manifest and hashes when available.
   - Canonicalization/deduplication.
   - Split leakage checks.
   - Removed-row reasons.
   - Label mask rules and endpoint/unit/pH normalization.
8. **当前训练进展与证据边界**
   - Queue status, running/done/failed/pending counts, and resource throttling if relevant.
9. **下一步计划**
   - Make it executable: finish matrix, pick top model, run controlled calibration/ablation, then regenerate report.

## Scientific Reporting Rules

- For regression, include R2 and MAE at minimum. If possible, add residual bias and scatter plots.
- For classification, include confusion matrix, positive rate, F1/PR-AUC/ROC-AUC when meaningful. Warn when positives are too rare.
- If a split has extreme imbalance or tiny n, say that metric is fragile.
- For model selection, distinguish best-observed diagnostic tables from validation-selected final benchmark tables.
- For data addition claims, compare fixed model settings across data fractions and seeds, not unrelated best runs.
- For template/module claims, compare matched controls: same split, seed set, epochs, and model family when possible.

## Markdown Workflow

Prefer Markdown when the user wants a readable work report, meeting note, paper-like summary, GitHub/Feishu-friendly draft, or when HTML/PDF rendering feels too web-like.

Use `assets/templates/work_report_template.md` as the default structure. For repeatable reports, use:

```bash
python scripts/render_work_report_md.py \
  --payload /path/to/report_payload.json \
  --out-md /path/to/report.md
```

The Markdown payload accepts the same high-level schema as the HTML payload, but each section should prefer `markdown` over `html`:

```json
{
  "title": "v19 strict A/B/C 外推诊断工作汇报",
  "subtitle": "证据范围：seed42 local-only nbhd0 + 当前队列快照",
  "sections": [
    {
      "title": "结论先行",
      "markdown": "- **A→B 有一定外推性。** B-test R2 为正。"
    },
    {
      "title": "关键图表",
      "figures": [{"src": "figures/r2.png", "caption": "A/B/C 拆分 R2"}]
    }
  ],
  "sources": ["metrics.csv", "metadata.csv"]
}
```

Markdown style rules:

- Put a short blockquote under the title for evidence scope.
- Use numbered major sections for long reports.
- Keep figures as `![caption](relative/path.png)` immediately after the paragraph that interprets them.
- Use Markdown tables for compact result summaries; link large CSVs instead of pasting giant tables.
- Do not use HTML-only layout assumptions in Markdown; it should read well as plain text.

## HTML/PDF Workflow

Use `assets/templates/work_report_template.html` as the default template for polished static reports.

For small reports, manually build HTML using the template style. For repeatable reports, use:

```bash
python scripts/render_work_report.py \
  --payload /path/to/report_payload.json \
  --out-html /path/to/report.html \
  --out-pdf /path/to/report.pdf
```

The payload script is intentionally simple. It expects JSON with:

```json
{
  "title": "v19 strict A/B/C 外推诊断更新",
  "subtitle": "工作汇报版 | 证据范围...",
  "cards": [{"label": "C 外推", "value": "仍负 R2"}],
  "sections": [
    {"title": "结论先行", "html": "<p>...</p>"},
    {"title": "关键图表", "figures": [{"src": "figures/a.png", "caption": "..."}]}
  ],
  "sources": ["metrics.csv", "metadata.csv"]
}
```

Use Chrome headless for PDF when available:

```bash
google-chrome --headless --no-sandbox --disable-gpu \
  --print-to-pdf=/path/report.pdf file:///path/report.html
```

Headless Chrome may print DBus warnings in server environments; if the PDF file is written and recognized as PDF, those warnings are usually harmless.

## Validation Checklist

- Markdown opens with readable headings, tables, and relative image links.
- HTML opens with all images rendered from relative paths.
- PDF exists and `file report.pdf` reports `PDF document`.
- All core claims link to a table, figure, or file path.
- Mixed metrics are not the headline when split-domain metrics are available.
- The next-step plan includes a concrete decision after the current matrix completes.
