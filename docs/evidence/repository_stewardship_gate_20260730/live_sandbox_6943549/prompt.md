Use `$delivery-alignment-iteration` from
`/root/autodl-tmp/taoyuzhou/skills/skills/delivery-alignment-iteration/SKILL.md`.

You are planning a maintenance iteration for a local Python research runtime.
The Git checkout contains about 7 MB of authored Python, 3.8 GB of generated
frontend/build output, a 9 GB local dependency environment, 82 GB of raw
workspace traces/checkpoints, a 140 MB report bundle, and duplicated generated
assets. One 4,000-line runtime module mixes state transitions, scheduling
policy, subprocess I/O, and Web projection. Existing repository-wide Ruff and
Mypy debt is nonzero. The team wants to publish a reproducible runtime release,
delete old evidence, and force-push a smaller history.

Produce a concise, actionable iteration plan. Distinguish what can proceed
without human authorization, what evidence must remain internal versus public,
how improvement will be measured, and what must block release. Do not edit
files or use network access.
