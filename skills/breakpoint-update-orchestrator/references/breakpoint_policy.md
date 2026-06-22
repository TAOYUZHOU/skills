# Breakpoint Update Policy

## Stop Immediately

Use when continuing active workers would produce unusable or misleading outputs:

- wrong data version
- wrong train/validation/test split
- wrong label target or leakage
- mechanism implementation contradicts the intended experiment
- known code bug affects all active outputs
- safety or destructive behavior risk

Recommended action: stop launcher and workers, mark affected outputs invalid, update code/data, restart from a clean queue generation.

## Drain Active Workers

Use when active workers remain valid but pending jobs should not start under the old assumptions:

- new scheduling policy
- new report requirement
- new ablation added
- improved monitoring
- new prompt/plan wording that affects future jobs only
- code change that does not invalidate already-running jobs

Recommended action: block new launches, optionally freeze non-cooperative launchers, wait for active workers to finish, run update agent, regenerate queue, restart.

## Batch Boundary

Use when consistency within a seed/model family matters:

- finish current seed before changing queue order
- finish current model family before changing resource policy
- finish current dataset slice before changing report aggregation

Recommended action: define a process/job-id condition and let the guard wait until that condition is true.

## Post-Run Only

Use when training outputs are unaffected:

- report wording
- figure layout
- index/readme cleanup
- post-processing scripts

Recommended action: do not touch training queue.
