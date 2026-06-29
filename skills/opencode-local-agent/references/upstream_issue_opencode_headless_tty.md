# Upstream issue draft — OpenCode `run` hangs without TTY

**Target repo:** https://github.com/anomalyco/opencode/issues/new  
**Status:** 待提 (not yet filed)  
**Observed version:** `opencode-ai` npm **1.17.11** (2026-06-29)

---

## Title

`opencode run` hangs after `init` in headless / non-TTY environments (CI, nohup, agent shells)

---

## Environment

| Item | Value |
|------|-------|
| OS | Linux (AutoDL Ubuntu, kernel 5.15) |
| OpenCode | `opencode-ai@1.17.11` via `npm i -g opencode-ai` |
| Node | v20.20.2 |
| Shell | bash, **no controlling TTY** (`[ -t 1 ]` → false) |
| Backend | local OpenAI-compatible llama-server (optional; hang occurs before model call) |
| Proxy | `https_proxy=http://127.0.0.1:7890` (not required to reproduce hang) |

---

## Steps to reproduce

1. Install OpenCode:
   ```bash
   npm i -g opencode-ai
   opencode --version   # 1.17.11
   ```

2. Confirm stdout is **not** a TTY:
   ```bash
   [ -t 1 ] && echo TTY || echo NO_TTY   # NO_TTY
   ```

3. Run non-interactive prompt (documented automation path):
   ```bash
   timeout 60 opencode run \
     --pure \
     --dangerously-skip-permissions \
     --format json \
     -m local-llm/qwythos-q4 \
     "Reply with exactly: ok"
   ```

4. Optional: same with attach to headless server:
   ```bash
   opencode serve --port 4096 --hostname 127.0.0.1 &
   sleep 3
   timeout 60 opencode run \
     --attach http://127.0.0.1:4096 \
     --pure \
     --dangerously-skip-permissions \
     --format json \
     "Reply with exactly: ok"
   ```

5. With `--print-logs`, last lines before hang:
   ```
   message=init
   ```
   No further output until timeout.

---

## Expected behavior

Per [Non-interactive mode docs](https://opencode.ai/docs/cli/) / `opencode run --help`:

- Process prompt without launching TUI
- Auto-approve permissions when `--dangerously-skip-permissions` is set
- Emit assistant text (or JSON events with `--format json`) to stdout
- Exit 0 within reasonable time (seconds, not minutes)

Example expected stdout fragment (`--format json`):

```json
{"type":"text","part":{"type":"text","text":"ok"}}
```

---

## Actual behavior

- Process **blocks indefinitely after `init`** when stdout/stdin are not connected to a TTY
- `timeout 60` → exit **124**; external kill → exit **143**
- No assistant output on stdout
- Setting `CI=false` does **not** fix the hang
- `opencode serve` + `--attach` still hangs without TTY

---

## Workaround (confirmed)

Wrap with pseudo-TTY via `script(1)`:

```bash
script -q -c 'opencode run --pure --dangerously-skip-permissions --format json -m local-llm/qwythos-q4 "Reply with exactly: ok"' /dev/null
```

Completes in ~5s on same host.

Bundled in this skill: `scripts/verify_opencode_agent.sh`

---

## Suggested fix directions

1. Detect non-TTY in `opencode run` and skip TUI/spinner/terminal init paths
2. Document pseudo-TTY requirement explicitly if intentional
3. Add `--no-tty` / `--ci` flag that forces non-interactive init (similar to other CLIs)
4. Ensure `opencode serve` + `--attach` path works without pseudo-TTY for automation

---

## References

- Skill roadmap: [roadmap.md](./roadmap.md) § Upstream
- OpenCode repo: https://github.com/anomalyco/opencode (MIT)
