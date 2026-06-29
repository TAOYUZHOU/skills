---
name: opencode-local-agent
description: "Deploy a local GGUF LLM (llama-server) with single-slot long context, quantized KV, and Flash Attention; wire OpenCode as a coding agent via OpenAI-compatible API. Use when the user asks for OpenCode, local coding agent, llama-server long context, or connecting Qwythos/Qwen GGUF to an agent."
metadata:
  short-description: Local llama-server + OpenCode agent on OpenAI-compatible API
origin: personal-skills
harp_seed_domain: experiment_on_silicon
complements:
  - hf-hub
  - resource-aware-queue-scheduler
  - workspace-hygiene
---

# OpenCode Local Agent (llama-server + long context)

Deploy a **local OpenAI-compatible inference server** tuned for **single-user agent** work, then connect **[OpenCode](https://opencode.ai/)** as the coding agent front-end.

Default target model: **Qwythos-9B Q4_K_M** (`empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF`). Any llama.cpp-compatible GGUF with tool-calling support can substitute via env vars.

## When to use

- User wants a **local coding agent** (OpenCode) on GPU server or laptop
- Task needs **≥100k context** on a **single 48GB** class GPU
- HARP executor wants a **cheap local verifier** for simple filesystem / command / artifact checks
- Workflow: **download GGUF → start llama-server → verify API → write `opencode.json`**

Do **not** use for HARP webchat replacement, Gradio demos, or cloud HF Jobs training.

## Why HARP seeds this under `experiment_on_silicon`

HARP task domains are `exploration | report | experiment_on_silicon`. This skill touches **GPU inference + local model serve**, so the engine seed lives under `experiment_on_silicon` alongside `hf-train`, `hf-eval`, and `resource-aware-queue-scheduler`.

**Canonical copy for Cursor:** this personal skills repo (`TAOYUZHOU/skills`). HARP only mirrors it into `WORK_DIR/.cursor/skills/` at workspace init.

**Future HARP hook:** lightweight verifier tasks (read artifact, run gate script, confirm file exists) can call OpenCode against `:8080` without replacing the main HARP executor model. See [references/roadmap.md](references/roadmap.md) § HARP verifier path.

## Script paths

| Context | Prefix |
|---------|--------|
| Personal skills / Cursor global | `scripts/` relative to this skill folder |
| HARP workspace after seed | `.cursor/skills/opencode-local-agent/scripts/` |

Below uses `scripts/` — substitute the HARP prefix when running inside a seeded workspace.

## Roadmap (executor checklist)

| Phase | Goal | Done when |
|-------|------|-----------|
| **0** | Prerequisites | `llama-server` built with CUDA; GGUF on disk |
| **1** | Long-context server | `start_llama_server.sh` running; `/props` → `n_ctx≥102400`, `total_slots=1` |
| **2** | API smoke test | `verify_llm_api.sh` returns assistant text |
| **3** | OpenCode config | `setup_opencode_config.sh` writes project `opencode.json` |
| **4** | Agent validation | `verify_opencode_agent.sh` exits 0 (headless-safe) |
| **5** | Remote access (optional) | AutoDL maps **8080** or SSH tunnel; OpenCode `baseURL` updated |

Full narrative: [references/roadmap.md](references/roadmap.md)

## Audit (HARP workspaces only)

```bash
python scripts/record_skill_use.py --event start --reason "opencode local agent deploy"
python scripts/record_skill_use.py --event finish --artifact ".state/opencode_local_agent.json"
```

Write provenance to `.state/opencode_local_agent.json`: `model_id`, `gguf_path`, `llm_base_url`, `n_ctx`, `parallel`, `kv_cache_types`, `opencode_config_path`, `profile`.

## Phase 0 — Prerequisites

### Build llama-server (CUDA, once per host)

```bash
git clone --depth 1 https://github.com/ggml-org/llama.cpp "$LLAMA_CPP_ROOT"
export CUDA_HOME=/usr/local/cuda-12.8
export PATH="$CUDA_HOME/bin:$PATH"
cmake -S "$LLAMA_CPP_ROOT" -B "$LLAMA_CPP_ROOT/build" -DGGML_CUDA=ON -DLLAMA_CURL=ON
cmake --build "$LLAMA_CPP_ROOT/build" -j"$(nproc)" --target llama-server
```

### Download GGUF

Use **v3+** weights (2026-06-28 onward). Older GGUFs had a broken chat template that loops in agent harnesses — redownload if unsure:

```bash
hf download empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF \
  --include "Qwythos-9B-Claude-Mythos-5-1M-Q4_K_M.gguf" \
  --local-dir "$WORK_DIR/.cache/local-models/qwythos-9b-q4"
```

**GGUF embedded template:** the `.gguf` file stores a Jinja chat template in metadata (`tokenizer.chat_template`). llama-server reads it automatically — **do not** pass `--chat-template` or `--chat-template-file` for Qwythos unless debugging. Qwythos v3 embeds the Qwen3.5 tool-calling template (native `<tool_call><function=…>` format).

```bash
export GGUF_PATH="$WORK_DIR/.cache/local-models/qwythos-9b-q4/Qwythos-9B-Claude-Mythos-5-1M-Q4_K_M.gguf"
export LLAMA_SERVER="$LLAMA_CPP_ROOT/build/bin/llama-server"
export LLM_PORT=8080
```

## Phase 1 — Start long-context llama-server

```bash
bash scripts/start_llama_server.sh
```

**Default `PROFILE=longctx`:**

| Setting | Value | Why |
|---------|-------|-----|
| `-c` | `102400` | ≥100k agent context |
| `--parallel` | `1` | one KV cache — saves ~4× VRAM vs default 4 slots |
| `--cache-type-k/v` | `q8_0` | halve KV vs f16 |
| `--flash-attn` | `on` | long-context memory + speed |
| `-ngl` | `99` | full GPU offload |
| chat template | *(none — GGUF embedded Qwen3.5 v3)* | native tool calling + reasoning; **never** use plain `chatml` |
| `--reasoning-preserve` | `on` | keep `` blocks across multi-turn agent loops |

```bash
PROFILE=dev bash scripts/start_llama_server.sh   # 8k smoke
nohup bash scripts/start_llama_server.sh >> "$WORK_DIR/.state/llama_server.log" 2>&1 &
bash scripts/verify_llm_api.sh
```

### OOM fallback

1. `--parallel 1`
2. `CACHE_TYPE_K=q4_0 CACHE_TYPE_V=q4_0`
3. `CTX=65536`
4. vLLM backend (see roadmap)

## Phase 2 — Sampling defaults

```json
{"temperature": 0.6, "top_p": 0.95, "top_k": 20, "max_tokens": 4096}
```

## Phase 3 — OpenCode

Install (requires outbound HTTPS — see roadmap § Network egress):

```bash
npm i -g opencode-ai
```

Generate config:

```bash
bash scripts/setup_opencode_config.sh "$WORK_DIR"
cd "$WORK_DIR" && opencode
```

Remote API: set `LLM_BASE_URL=https://<proxy-host>/v1` before `setup_opencode_config.sh`.

## Phase 4 — Validate agent loop

Headless / CI (no TTY — required on AutoDL background shells):

```bash
bash scripts/verify_opencode_agent.sh "$WORK_DIR"
```

OpenCode `run` blocks during init without a TTY. The verify script wraps `script -q -c ...` (pseudo-TTY) plus `--pure --dangerously-skip-permissions --format json`.

Interactive (laptop terminal):

```bash
cd "$WORK_DIR" && opencode
```

Prompt: "List files in this directory and summarize README in 3 bullets"

## Network egress on AutoDL / restricted hosts

This host uses `https_proxy=http://127.0.0.1:7890` (local Clash/V2Ray). If `curl https://opencode.ai` fails with `SSL routines::unexpected eof`, it is usually **proxy instability mid-TLS-handshake**, not a hard firewall block.

Fallback order:

1. Retry with proxy env: `https_proxy=http://127.0.0.1:7890 curl -fsSL https://opencode.ai/install`
2. Install via npm (uses same proxy): `npm i -g opencode-ai`
3. Fetch install script from GitHub raw (redirect target): `curl -fsSL https://raw.githubusercontent.com/anomalyco/opencode/refs/heads/dev/install | bash`
4. SSH local forward from laptop (when proxy down):

```bash
# on laptop
ssh -L 8080:127.0.0.1:8080 user@gpu-host
# OpenCode on laptop points baseURL to http://127.0.0.1:8080/v1
```

5. SSH SOCKS egress (when npm/curl need laptop network):

```bash
ssh -D 1080 user@gpu-host   # on laptop, then on GPU host:
export ALL_PROXY=socks5h://127.0.0.1:1080
npm i -g opencode-ai
```

## Environment reference

| Variable | Default | Meaning |
|----------|---------|---------|
| `GGUF_PATH` | (required) | Path to `.gguf` weights |
| `LLAMA_SERVER` | `llama-server` | llama.cpp server binary |
| `LLM_PORT` | `8080` | API port |
| `PROFILE` | `longctx` | `longctx` or `dev` |
| `REASONING_PRESERVE` | `on` | pass `--reasoning-preserve` to llama-server (`off` to disable) |
| `LLM_BASE_URL` | `http://127.0.0.1:8080/v1` | OpenCode provider URL |

Reference deployment: `/root/autodl-tmp/taoyuzhou/qwythos-local/`.
