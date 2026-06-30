# Multimodal (vision) — Qwythos on llama-server

Qwythos-9B inherits **Qwen3.5-9B vision** from base. Multimodal inference in llama.cpp needs **two GGUF files**:

| File | Role | Size (approx) |
|------|------|----------------|
| `Qwythos-9B-Claude-Mythos-5-1M-Q4_K_M.gguf` | Text weights | ~5.6 GB |
| `mmproj-Qwythos-9B-Claude-Mythos-5-1M-F16.gguf` | Vision encoder + projector | ~0.9 GB |

Text-only deploy (default agent path) loads only the first file. **Image input requires both** plus `--mmproj` on `llama-server`.

## Honest capability note

Qwythos SFT was **text-only** — vision behavior is **unchanged from Qwen3.5-9B base**. Good for OCR, charts, UI screenshots; not independently benchmarked as "Qwythos vision". Validate on your use case.

OpenCode / HARP verifier path remains **text + tools** unless you explicitly add vision to the client.

---

## 1. Download mmproj

```bash
bash scripts/download_mmproj.sh
# or set MODELS_DIR=/path/to/models
```

Manual:

```bash
hf download empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF \
  --include "mmproj-Qwythos-9B-Claude-Mythos-5-1M-F16.gguf" \
  --local-dir "$WORK_DIR/.cache/local-models/qwythos-9b-q4"
```

Community `mmproj-*-F16.gguf` for **Qwen3.5-9B** also works (same vision tower).

---

## 2. Start llama-server with vision

`start_llama_server.sh` auto-detects mmproj next to the text GGUF:

- `$WORK_DIR/.cache/local-models/qwythos-9b-q4/mmproj-*.gguf`
- `$WORK_DIR/../qwythos-local/models/mmproj-*.gguf`

Or set explicitly:

```bash
export MMPROJ="$WORK_DIR/.cache/local-models/qwythos-9b-q4/mmproj-Qwythos-9B-Claude-Mythos-5-1M-F16.gguf"
bash scripts/start_llama_server.sh
```

Equivalent manual flags:

```bash
llama-server \
  -m Qwythos-9B-Claude-Mythos-5-1M-Q4_K_M.gguf \
  --mmproj mmproj-Qwythos-9B-Claude-Mythos-5-1M-F16.gguf \
  -c 102400 --parallel 1 --flash-attn on \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --reasoning-preserve
```

**Do not** pass `--chat-template chatml` — use GGUF-embedded Qwen3.5 v3 template.

---

## 3. Verify vision is loaded

```bash
curl -s http://127.0.0.1:8080/props | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["modalities"])'
# expect: {"vision": true, "video": false, "audio": false}
```

Or:

```bash
bash scripts/verify_vision_api.sh
```

---

## 4. API shape (OpenAI-compatible)

POST `/v1/chat/completions` with typed `content`:

```json
{
  "model": "qwythos-q4",
  "messages": [{
    "role": "user",
    "content": [
      {"type": "text", "text": "Describe this image."},
      {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
    ]
  }],
  "max_tokens": 512,
  "temperature": 0.6,
  "top_p": 0.95
}
```

`image_url.url` may also be `https://...` or `file://...` (with llama-server `--media-path`).

---

## 5. Web chat UI (:8788)

Reference implementation: `qwythos-local/` in the workspace.

```bash
# inference :8080 (with mmproj)
nohup bash start_server.sh >> server.log 2>&1 &

# UI + same-origin /v1 proxy :8788
nohup bash start_chat_ui.sh >> chat_ui.log 2>&1 &
```

UI behavior:

- Fetches `/api/props` → shows **「视觉已启用」** when `modalities.vision=true`
- 🖼 button uploads jpeg/png/gif/webp as base64 `image_url`
- Disabled with banner when mmproj not loaded

AutoDL: map **8788** only (UI proxies API).

---

## 6. VRAM impact

Vision adds ~0.9 GB projector + image token KV during encode. On 48 GB with 100k text ctx + q8 KV, monitor with `nvidia-smi` after first image request. OOM ladder: lower `CTX`, then `q4_0` KV, then disable vision for agent-only workloads.

---

## 7. What is not covered

| Modality | llama-server | This skill UI |
|----------|--------------|---------------|
| Image | ✅ with mmproj | ✅ web chat |
| Audio | API only | ❌ |
| Video | API only | ❌ |
| OpenCode agent | text + tools default | ❌ vision not wired |
