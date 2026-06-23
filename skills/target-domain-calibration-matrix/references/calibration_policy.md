# Calibration Policy

## Data Roles

- `source_train`: source-domain rows allowed for training.
- `source_eval`: source-domain rows used only for A/B evaluation.
- `target_calibration_pool`: target-domain rows eligible for controlled addition to training.
- `target_calibration_train`: selected target-domain rows for one calibration setting.
- `target_calibration_unused`: eligible target rows not selected for that setting.
- `target_heldout_test`: immutable target-domain rows never used for training, model selection, or residual-driven sampling.

## Leakage Rules

- Split target groups before choosing calibration sizes.
- Prefer scaffold-level target holdout when scaffold labels are available; otherwise use molecule-level holdout.
- Do not use target held-out residuals for error-driven sampling.
- Do not tune sampling strategy by repeatedly optimizing on the same target held-out test without reporting that limitation.

## Recommended Comparison

For each fixed architecture and seed, compare:

1. Source-only baseline.
2. Random target calibration.
3. Scaffold-diverse target calibration.
4. Low-similarity frontier target calibration.
5. Template/source balanced target calibration when metadata supports it.

Success requires target held-out improvement with A/B guardrails, not just mixed-test improvement.
