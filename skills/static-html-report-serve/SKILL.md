---
name: static-html-report-serve
description: >-
  Expose a directory of static HTML reports (slides, milestone docs) on AutoDL
  custom service port 6006 for LAN/public access and Feishu links. Start/stop
  python http.server, print public URL from AutoDLService6006URL, sync to Mac.
  Use when sharing retro-engine or HARP HTML reports with colleagues via URL.
metadata:
  short-description: Serve static HTML reports on AutoDL public port 6006
---

# Static HTML Report Serve

Use when the user wants colleagues to open an **interactive HTML slide** or report via a **clickable URL** (Feishu chat/doc), instead of uploading zip/PDF.

This skill wraps `python3 -m http.server` behind AutoDL's **自定义服务 6006** reverse proxy (`AutoDLService6006URL`).

## When to use

- After rendering/updating `report/*.html` (slides, milestone report, process doc)
- User asks to「暴露到公网 / 局域网」「飞书链接」「同事能点开 HTML」
- **Not** for secrets, credentials, or draft-only artifacts

## Dependencies

- Python 3 (stdlib `http.server`)
- AutoDL instance with **自定义服务 → 6006** enabled (default on many images)
- Env var `AutoDLService6006URL` (set by AutoDL when instance is running)

## Quick start (retro-engine report tree)

```bash
SKILL=/root/autodl-tmp/taoyuzhou/skills/skills/static-html-report-serve

# Start (or print status if already running)
"$SKILL/scripts/serve_html_report.sh" \
  --dir /root/autodl-tmp/taoyuzhou/report \
  --entry retro_engine_work_report_slides.html

# Stop
"$SKILL/scripts/serve_html_report.sh" --stop --dir /root/autodl-tmp/taoyuzhou/report

# Status + curl smoke test
"$SKILL/scripts/serve_html_report.sh" --status --dir /root/autodl-tmp/taoyuzhou/report
```

Copy the printed `https://u*.seetacloud.com:8443/...` link into Feishu.

## Workflow

1. **Update content** — edit Markdown/canonical source, re-render HTML, run `bundle_slides_for_feishu.py` if GIF assets changed.
2. **Prefer a dedicated publish tree** — serve only files meant for readers (see Risks).
3. **Start server** — `serve_html_report.sh --dir ... --entry main.html`
4. **Verify** — script curls localhost; user opens public URL once in browser.
5. **Share link** — Feishu message/doc; note expiry conditions below.
6. **Optional Mac sync** — `rsync_report_from_autodl_on_mac.sh` (pull on Mac) or `sync_report_to_mac.sh` (push if Mac SSH reachable).

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/serve_html_report.sh` | start / stop / status; prints public URL |
| `scripts/check_slide_density.py` | Playwright gate: visual fill ratio on key slides |
| `assets/html-slide-clarity-checklist.md` | Layout + completeness checklist before publish |
| `assets/sync_mac.local.conf.example` | Mac push target template |
| `assets/feishu_link_snippet.md` | Copy-paste template for Feishu |

Project-local thin wrappers (optional):

- `report/serve_retro_report.sh` → calls this skill with `--dir report`

## CLI reference

```bash
serve_html_report.sh [--dir PATH] [--port PORT] [--entry FILE.html] [--stop|--status]
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--dir` | required | Directory to serve (document root) |
| `--port` | `6006` | Bind port; must match AutoDL custom service |
| `--entry` | `index.html` | Primary file for public URL hint |
| `--stop` | — | Kill server for this dir (pidfile per dir) |
| `--status` | — | Print pid, log tail, public URLs |

Pid/log files live **inside `--dir`**: `.report_http.pid`, `.report_http.log` (gitignore these).

## Risks (read before sharing publicly)

| Risk | Severity | Mitigation |
|------|----------|------------|
| **No authentication** | High | Anyone with URL can read **every file** under `--dir` |
| **Directory listing** | Medium | `http.server` lists files if no index; keep `--dir` minimal |
| **Over-broad tree** | High | Do **not** serve repo root or `report/` with hygiene JSON, drafts, logs. Use a `publish/` subdir or whitelist copy |
| **Internal paths in HTML** | Low | HTML may cite `/root/autodl-tmp/...` in footnotes — review before share |
| **Instance = public host** | Medium | URL points at your GPU box; DDoS/scrape loads hit your instance |
| **No HTTPS on origin** | Low | AutoDL proxy terminates TLS; traffic user→seetacloud is encrypted |
| **Stale content** | Low | URL stays valid but shows old HTML until you re-render (not a security issue) |

**Recommended:** create `report/publish/` with only:

- `index.html`, `*_slides.html`, `*_standalone.html`, `assets/` needed by slides

Then `--dir report/publish`.

## When the link / slides stop working

| Event | Symptom | Fix |
|-------|---------|-----|
| **AutoDL 实例关机 / 释放** | URL timeout / connection refused | 开机后重新 `serve_html_report.sh` |
| **实例重建 / 换机器** | Old `u807812-....seetacloud.com` **永久失效** | 新实例新 URL；更新飞书链接 |
| **HTTP 进程退出** | 404 or connection refused | `--status`; restart serve |
| **自定义服务 6006 未开** | Public URL 404, localhost OK | AutoDL 控制台打开 6006 映射 |
| **改了 `--port`** | Public URL wrong | Use 6006 or update console mapping |
| **删除了 HTML 或 assets/** | 404 on slide; GIF/static broken | Re-render + bundle; fix relative paths |
| **只更新了 MD 没渲染 HTML** | Page loads but content old | Re-run render-html / bundle script |

**Slides do not "expire" by time** — they fail when **host, process, or files** go away. Content can be outdated while URL still works.

## Agent guidelines

- Always run `--status` before claiming a link is live.
- After updating reports, re-run serve only if process died; refreshing files does **not** require restart.
- Print **both** entry URL and index URL for Feishu.
- Warn user if `--dir` contains non-public files (logs, `.json` audits, `.conf` with hosts).
- For Mac sync: prefer pull script on Mac unless `sync_mac.local.conf` exists with reachable `MAC_HOST`.
- Do not commit `sync_mac.local.conf` or pid/log files.
- **HTML slides:** design at **1920×1080** fixed canvas + JS `scale(min(vw/1920,vh/1080))`. Do **not** size slide content with raw `vw`/`vh` — browser full-screen will shrink content and expand whitespace vs IDE preview.
- **Clarity / density:** before sharing URLs, run `scripts/check_slide_density.py` on the HTML. Flowcharts and diagrams must use `.slide.dense` + `.svg-wrap.flowchart` (or `.img-wrap.hero`) so the primary visual fills ≥52% of slide height. See `assets/html-slide-clarity-checklist.md`. If content does not fit at readable size, **split slides** — never shrink diagrams to fit bullet lists.

## Related

- Render: HARP `render-html` skill
- Bundle GIF slides: `report/bundle_slides_for_feishu.py`
- Sync EC2 code: `rsync-remote-sync` skill
