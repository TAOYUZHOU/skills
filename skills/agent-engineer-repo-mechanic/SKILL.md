---
name: agent-engineer-repo-mechanic
description: >-
  Personal, lightweight iteration workflow for continuously improving a
  repository with an agent acting as the "mechanic". Includes an elegant
  general-purpose webapp template (FastAPI backend + single-page frontend) and
  an AGENTS.md that drives the mechanic's optimization loop. Use when building
  or evolving a personal repo with a web UI, when the user wants a reusable
  repo skeleton with front/back interaction, or when a small agent should keep
  improving a codebase over many turns with evidence, checkpoints, and
  convergence instead of an unbounded chat.
---

# Agent Engineer Repo Mechanic

A small, elegant iteration workflow for one agent ("mechanic") that owns a
repository and keeps improving it across many turns. It is the lightweight
sibling of `delivery-alignment-iteration`: same discipline (small bounded
changes, evidence, checkpoints, convergence), without the full R3 proof chain.

## When to use

- You want a reusable personal repo skeleton with a working front/back
  interaction and an `AGENTS.md` that tells the agent how to run itself.
- A small agent should keep optimizing a codebase over multiple turns with a
  visible state, evidence, and stopping conditions.
- You want the "mechanic" loop for personal projects: observe -> hypothesize ->
  change -> verify -> record -> converge.

When the work touches authority, releases, or cross-workspace recovery, switch
to the full `delivery-alignment-iteration` skill instead.

## The mechanic's loop (one tick)

Every tick is a bounded, recorded unit of work:

1. **Observe** -- read `state.json`, run the app's health/self-check, list
   evidence, note the current frontier (what is unfinished or failing).
2. **Hypothesize** -- pick ONE bounded change and write it down before editing.
3. **Change** -- make the smallest edit that tests the hypothesis.
4. **Verify** -- run the tests and the self-check; capture concrete evidence
   (output, hashes, before/after).
5. **Record** -- append one entry to `state.json` (hypothesis, diff summary,
   evidence refs, result) and update the frontier.
6. **Checkpoint** -- every N ticks (default 3) write a checkpoint note and, if
   the budget or risk threshold is crossed, pause for human input.

The loop is a state machine, not a chat: state drives the next tick, and a tick
never claims completion without recorded evidence.

## Convergence and stopping

A task converges when its declared acceptance criteria are all met with
recorded evidence and the remaining items are explicitly classified. Stop
conditions:

- all acceptance criteria met and verified;
- budget exhausted (ticks or tokens) -- pause for human decision, never
  convert failure into acceptance;
- a change fails verification twice in a row for the same hypothesis -- record
  the finding, retire the hypothesis, and move to the next one;
- a human checkpoint request is open.

## Contract lite (optional, recommended for multi-day work)

For anything beyond a single sitting, write a one-screen contract at the repo
root (`CONTRACT.md`) with: intent, non-goals, acceptance criteria (observable),
verification commands, and stopping conditions. The mechanic must not expand
scope past the contract without a new human-approved version.

## Templates

`templates/webapp/` is a ready-to-run general webapp skeleton:

- `app.py` -- FastAPI backend: health, state, and iteration endpoints.
- `frontend/index.html` -- single-file page: live state, health, iteration
  log, and a submit form (no build step).
- `AGENTS.md` -- the mechanic's operating manual for this repo (loop, rules,
  evidence, budgets, convergence).
- `state.json`, `evidence/`, `tests/`, `run.sh`, `requirements.txt`.

Copy the template, run `bash run.sh`, open `http://127.0.0.1:8000`, then let
the mechanic work per `AGENTS.md`. Details on the loop and optimization
dynamics: [`references/mechanic-dynamics.md`](references/mechanic-dynamics.md).

## Mechanics' rules (non-negotiable, from the full skill, kept small)

- A plan is not a fix; a green test is not proof of an untested boundary.
- Evidence lives in `evidence/` with hashes; prose in chat is not evidence.
- Small steps, one hypothesis per tick, rollback via git, never delete
  evidence or history.
- Record residual risk honestly; a checkpoint that says "blocked" is a first
  class result, not a failure.
- When the iteration touches release/authority semantics, escalate to
  `delivery-alignment-iteration`.
