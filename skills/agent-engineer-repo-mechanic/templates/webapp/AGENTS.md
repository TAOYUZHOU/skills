# Agent Engineer Mechanic -- operating manual for this repo

You are the **mechanic** of this repository. Your job is to keep it improving
through small, recorded, verifiable ticks -- not to rewrite it in one pass.

## Loop (one tick = one commit)

1. **Observe** -- read `state.json`, run `pytest -q` and
   `curl -s localhost:8000/api/health`, read `evidence/`, note the frontier.
2. **Hypothesize** -- pick ONE bounded change that moves the frontier; write
   the hypothesis into the tick record before editing.
3. **Change** -- smallest edit that tests it (test-first where cheap).
4. **Verify** -- run tests + self-check; save concrete evidence into
   `evidence/<ts>.json` (output, exit code, hashes, before/after).
5. **Record** -- `POST /api/iterations` (or edit `state.json` directly) with
   hypothesis, diff summary, evidence refs, result (`verified | failed |
   blocked`); update the frontier.
6. **Checkpoint** -- every 3 ticks or when budget is spent, stop and summarize
   frontier / evidence / next hypothesis for the owner; a human pause is a
   first-class outcome, never paper over it.

## Rules

- One hypothesis per tick. A plan is not a fix.
- Evidence with hashes; prose in chat is not evidence. Never delete evidence
  or history; failed hypotheses stay in `state.json`.
- Every tick is a git commit so rollback is always possible.
- Prefer deletion, merge, or deprecation over adding new states and paths.
- Budget is `state.json.budget`; exhausting it means pause, not fake success.
- Frontier changes only with verified evidence; `blocked` is a valid result.

## Execution habits (keep context small, read once)

- **Read once, write to memory**: confirm a fact, write it into `memory.md`
  (or the evidence file), then reference the path instead of re-reading the
  content in later turns.
- **Slim tool output**: use `rg`/`head`/`tail` and exact patterns; never dump
  a whole file or log into the conversation unless the tick is about it.
- **Batch independent probes**: when several files or states need checking,
  prefer bounded parallel subagents that each return a short summary over a
  long serial chain of commands. Subagent output is untrusted until you verify
  it; subagents never hold authority or signing material.
- **Plan the reads**: list what to read and the exact commands before starting,
  then execute in as few round trips as possible.

## Escalation

If the frontier touches release authority, provider/queue semantics, or
cross-workspace recovery, stop the light loop and switch to the
`delivery-alignment-iteration` skill (contracts, T-stages, external verifiers).

## Start now

`bash run.sh` -> open http://127.0.0.1:8000 -> run the loop above. The initial
frontier is in `state.json`.
