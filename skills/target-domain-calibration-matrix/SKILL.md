---
name: target-domain-calibration-matrix
description: Use when designing target-domain calibration or domain-transfer experiment matrices for ML/chemistry models, especially when adding different amounts of C-like or target-domain data to training while preserving held-out A/B/C tests, preventing leakage, comparing sampling strategies, fixing top architectures and hyperparameters, and producing queue JSON for resource-aware training.
metadata:
  short-description: Design leakage-safe target-domain calibration experiment matrices
---

# Target-Domain Calibration Matrix

Use this skill when the scientific question is no longer "which model architecture is best?" but "does adding a controlled amount of target-domain data improve target-domain generalization without hurting source-domain performance?"

This skill designs the experiment. It should hand off execution to `resource-aware-queue-scheduler` and reporting to `academic-experiment-work-report`.

## Core Contract

- Never let target-domain calibration rows leak into the final target held-out test.
- Split target-domain data by molecule/scaffold group before sampling calibration sizes.
- Keep A-test, B-test, and target/C-test permanently separate.
- Fix model architectures and hyperparameters before comparing calibration strategies.
- Compare data strategy effects with matched seeds, model settings, epochs, and evaluation splits.
- Write a matrix manifest, split assignment files, queue JSON, and a lock note before training starts.

## Workflow

1. **Define domains and immutable tests**
   - Source/train domains: usually A and B.
   - Target domain: usually C or C-like data.
   - Split target data into `target_calibration_pool` and `target_heldout_test` by molecule or scaffold group.
   - Existing A/B tests should remain unchanged unless the user explicitly asks for a new split.

2. **Choose fixed model candidates**
   - Use only the top architectures from the previous locked benchmark.
   - Keep hyperparameters, epochs, seeds, and preprocessing fixed.
   - Do not reopen the full architecture search unless the user asks for it.

3. **Choose calibration size ladder**
   - Recommended first ladder: `0, 0.5%, 1%, 2.5%, 5%, 10%, 20%` of the target calibration pool.
   - For small target pools, also include absolute molecule counts such as `k=8,16,32,64`.
   - Sample by molecule/scaffold group, not by raw row, unless row-level sampling is scientifically justified.

4. **Choose sampling strategies**
   - `random`: baseline calibration value.
   - `scaffold_diverse`: maximize scaffold coverage.
   - `low_similarity_frontier`: prioritize target molecules far from source train by max Tanimoto.
   - `template_family_balanced`: balance dominant template families.
   - `source_protocol_balanced`: balance source/protocol labels when available.
   - `error_driven`: only after a prior model has out-of-fold residuals; do not use held-out test residuals.

5. **Define success criteria before running**
   - Primary: target held-out half-life R2 increases and MAE decreases across seeds.
   - Guardrails: A-test and B-test do not materially regress.
   - Diagnostics: gains appear across scaffold novelty, Tanimoto quantile, template family, and source/protocol strata.
   - Report mean/median and seed variance; best-observed single runs are diagnostic only.

6. **Generate artifacts**
   - `calibration_matrix_manifest.csv`: one row per planned setting.
   - `splits/<job_id>.csv`: row-level assignment for train/calibration/heldout/eval.
   - `calibration_queue.json`: queue compatible with `resource-aware-queue-scheduler`.
   - `CALIBRATION_MATRIX_LOCK.md`: design assumptions, target split, sampling strategies, model candidates, and success metrics.

## Scripted Start

Use the bundled script when the metadata table has at least an ABC/domain column and a molecule identifier or SMILES column:

```bash
python scripts/build_calibration_matrix.py \
  --metadata /path/to/metadata.csv \
  --out-dir /path/to/calibration_matrix \
  --domain-col abc_set \
  --target-domain C \
  --source-domains A B \
  --holdout-frac 0.5 \
  --calibration-fracs 0 0.005 0.01 0.025 0.05 0.10 0.20 \
  --strategies random scaffold_diverse low_similarity_frontier template_family_balanced \
  --seeds 42 43 44 \
  --architecture-config /path/to/top_architectures.json \
  --command-template /path/to/train_command_template.json
```

If no command template is provided, the script still writes split files and a manifest; write the queue manually afterward.

## Hand-Off

- After matrix generation: run `resource-aware-queue-scheduler` on `calibration_queue.json`.
- During a running queue: use `breakpoint-update-orchestrator` if sampling strategy, data, or model assumptions change.
- After completion: use `academic-experiment-work-report` and report A/B/C separately, with target held-out diagnostics.

## Validation Checklist

- Target held-out groups do not appear in any training/calibration split.
- Calibration size `0` is a true no-target-data baseline.
- Every nonzero calibration setting has matched model candidates and seeds.
- Queue job IDs include architecture, strategy, fraction or k, and seed.
- The lock file states whether sampling was molecule-level or scaffold-level.
- Report claims compare matched settings, not unrelated best runs.
