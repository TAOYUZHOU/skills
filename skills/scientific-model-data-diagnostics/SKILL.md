---
name: scientific-model-data-diagnostics
description: Use before interpreting scientific modeling experiments, including regression, classification, reinforcement learning, active learning, domain transfer, chemistry, biology, materials, robotics, or simulation tasks, when metrics may be affected by data-generating context, domain shift, label or reward quality, target distribution, split leakage, class imbalance, residual bias, novelty/similarity structure, protocol or environment variables, policy/action coverage, or small-sample strata. Produces diagnostic tables and figures that should feed scientific reports.
metadata:
  short-description: Diagnose scientific model results through data, domain, target, context, and residual structure
---

# Scientific Model Data Diagnostics

Use this skill before drawing conclusions from scientific modeling results, especially when performance may reflect data structure, experimental context, sampling policy, or target quality more than architecture quality.

## Core Contract

Separate model capability from data and split effects.

- Never explain a metric from aggregate R2/F1 alone when split/domain metadata exist.
- Always inspect target support, target variance, residual/bias structure, and sample size for each important stratum.
- Treat high error, negative R2, rare-class failure, reward instability, and surprising subgroup behavior as data-diagnosis questions before model-blame questions.
- Report whether each metric is reliable, fragile, or not scientifically interpretable.
- Save diagnostics as durable CSV/PNG artifacts and feed them into the final experiment report.

## When To Run

Run this skill for scientific model reports when any of these are true:

- Domain splits exist, such as train/source/target, A/B/C, time split, protocol split, geography/site split, simulation-to-real split, patient/batch split, or scaffold/family split.
- The task is condition-sensitive, protocol-sensitive, or environment-sensitive.
- Regression R2 differs from MAE/RMSE conclusions.
- Classification positives are rare, missing, or uneven across splits.
- Reinforcement learning or active learning results depend on reward coverage, action/policy coverage, episode context, exploration strategy, simulator version, or intervention cost.
- There are context/protocol fields, measurement sources, environment variables, data collection modes, operators, instruments, simulators, cohorts, or missingness patterns.
- There are representation, novelty, or neighborhood fields such as clusters, families, nearest-neighbor distance, embedding distance, retrieval similarity, structural similarity, or template/mechanism groups.
- The user asks why a model generalizes or fails.

## Required Diagnostic Pass

1. **Evidence Scope**
   - Completed jobs, seeds, model setting, official evaluation split, prediction files, and metadata files.
   - State whether this is full matrix evidence or a priority/pilot subset.
2. **Metric Reliability**
   - For regression: R2, MAE, RMSE, residual mean, target mean, target standard deviation, and n.
   - For classification: positives, positive rate, confusion matrix, F1/accuracy, and a warning when a class is absent.
   - For reinforcement learning or policy tasks: return/reward distribution, success rate, episode count, action coverage, reward sparsity, off-policy/on-policy mismatch, and environment coverage.
   - Flag R2 as fragile when n is small or label variance is narrow.
3. **Split And Domain Diagnostics**
   - Compute metrics separately for each official domain/split.
   - Do not let mixed test metrics drive the conclusion.
4. **Data-Generating Context Diagnostics**
   - Stratify by variables that describe how, where, under what protocol, or under what environment the target was generated.
   - Treat missingness and imputed defaults as first-class strata.
5. **Representation/Novelty Diagnostics**
   - Stratify by variables that describe similarity, novelty, cluster/family membership, mechanism group, neighborhood density, or distance from the training distribution.
   - Interpret similarity cautiously: a representation can say two examples are near while the true target mechanism or context differs.
6. **Residual Inspection**
   - List largest absolute residuals and systematic bias by stratum.
   - Check whether errors are overprediction, underprediction, or condition-specific.
7. **Data-Driven Next Actions**
   - Recommend split fixes, calibration sampling, metadata enrichment, label cleaning, or targeted experiments before proposing architecture changes.

## General Diagnostic Axes

Use these axes first; task-specific fields are examples under the axes, not the organizing principle.

- **Target structure**: label/reward range, variance, censoring, bounds, class balance, reward sparsity, observation noise, repeated measurements.
- **Data-generating context**: protocol, environment, source, instrument, simulator, cohort/site, operator, time, intervention setting, missingness/imputation.
- **Domain and split structure**: source/target split, train/test leakage, temporal or group leakage, calibration pool versus heldout, distribution shift.
- **Representation and novelty**: nearest-neighbor distance, cluster/family, mechanism group, embedding distance, retrieval similarity, density, extrapolation distance.
- **Model residual behavior**: signed bias, absolute error, heteroscedasticity, failure clusters, outliers, calibration error, over/underprediction.
- **Decision or policy coverage**: action coverage, policy support, exploration strategy, episode context, reward definition, simulator/real-world mismatch.

## Interpretation Rules

- If a stratum has lower MAE but worse R2, check label variance; narrow label ranges can make R2 look bad.
- If high-similarity samples fail, look for context mismatch, mechanism mismatch, local sensitivity, duplicate protocol rows, or narrow target range.
- If low-similarity samples have positive R2 but higher MAE, the model may be capturing coarse target range rather than precise local behavior.
- If a classification split has zero positives or zero negatives, mark classification conclusions as unavailable for that split.
- If an RL/policy benchmark has poor action or environment coverage, do not treat average return as robust deployment evidence.
- If metadata are missing, make missingness a diagnostic stratum; do not silently drop it.

## Domain Examples

Examples help map the general axes to concrete scientific tasks:

- **Chemistry/materials**: pH, temperature, solvent, buffer, endpoint type, units, assay/source, scaffold, fingerprint similarity, template/mechanism family, matched-template count, molecular size.
- **Biology/medicine**: assay protocol, cell line, species, tissue, batch, lab/source, patient cohort, dose, time point, missingness, repeated measurement id.
- **Robotics/RL/simulation**: simulator version, task family, initial state distribution, action bounds, controller/policy family, reward components, episode length, real versus simulated domain.
- **Time-dependent science**: collection date, forecast horizon, seasonality, sensor/instrument id, station/site, intervention timing.

## Script Workflow

Use `scripts/run_scientific_model_data_diagnostics.py` when predictions and metadata are in CSV files.

```bash
python scripts/run_scientific_model_data_diagnostics.py \
  --predictions /path/test_predictions.csv \
  --metadata /path/materialized_metadata.csv \
  --out-dir /path/analysis/diagnostics \
  --join-key sample_idx \
  --filter official_eval_role=target_heldout \
  --target-col target_value \
  --pred-col predicted_value \
  --mask-col target_mask \
  --group-cols domain_split context_field protocol_field novelty_bin family_or_cluster \
  --class-target-col class_label \
  --class-prob-col class_probability \
  --class-mask-col class_mask
```

Replace the placeholder columns with task-local fields. For a chemistry hydrolysis task, for example, `context_field` may be pH or temperature, `family_or_cluster` may be template family or scaffold family, and `novelty_bin` may be Tanimoto quantile.

The script writes:

- `regression_group_diagnostics.csv`
- `classification_group_diagnostics.csv` when class columns are provided
- `top_residuals.csv`
- `diagnostic_summary.json`
- Optional PNG figures when matplotlib is available

For complex experiment matrices, run the script per selected job or build a small wrapper that loops over jobs and then aggregate the output.

## Report Handoff

When handing diagnostics to `academic-experiment-work-report`, include:

- One paragraph explaining which metric claims are reliable or fragile.
- A table of the most important domain/condition/similarity strata.
- One residual or subgroup figure.
- Data-driven next actions, such as condition-aware calibration sampling or split redesign.

Do not allow the report to present model rankings without mentioning data diagnostics when these diagnostics materially change interpretation.
