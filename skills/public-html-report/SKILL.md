---
name: public-html-report
description: >-
  Author beautiful static HTML (slide decks via beautiful-html-templates workflow,
  or single-page reports) and publish day-stable public URLs with HTTP Basic Auth
  and nginx on a fixed IP (not trycloudflare). Use when sharing eval results,
  experiment writeups, comparison matrices, tech-share decks, dashboards; when
  the user asks for a public URL, fixed IP, reverse proxy, template pick/preview,
  beautiful HTML slides, or to publish a report.
metadata:
  short-description: Beautiful HTML authoring + authenticated public publish
---

# Public HTML Report

End-to-end skill: **author** a share-ready static HTML artifact, then **publish**
it read-only with auth and a day-stable public URL.

Domain-specific content (e.g. retrosynthesis trees) lives in separate skills;
**this skill owns visual quality + publish + security**.

## When to use

- Report / HTML / comparison page / slide deck **visible on the public internet**
- 「给个链接给同事看」、day-stable URL、固定公网 IP、反向代理
- Beautiful HTML slides, 选模版、标题页预览、tech-share deck
- Replacing ephemeral `*.trycloudflare.com` tunnels

## Template library (external)

Slide templates are **not** vendored in this skill. Resolve the library:

1. Prefer `/root/autodl-tmp/taoyuzhou/beautiful-html-templates`
2. Else any local clone the user names
3. Else `git clone https://github.com/zarazhangrui/beautiful-html-templates`

Authoritative detail: that repo's `AGENTS.md`. Skill summary: [reference-templates.md](reference-templates.md).

## Pipeline

```
A. Author
   A1. Choose path: slide deck (templates) OR single-page report (visual bar)
   A2. Build self-contained static site (no server-side code; no secrets)
B. Publish
   B1. Serve read-only + Basic Auth (loopback or behind nginx only)
   B2. Expose: nginx :80 → auth backend (EC2) OR AutoDL 6006 (see Related)
   B3. PUBLIC_URL.txt + credentials out-of-band
   B4. Verify: curl -u USER:PASS → 200
```

---

## A) Author

### A1. Choose artifact path

| Path | Use when | How |
|------|----------|-----|
| **Slide deck** | Tech share, narrative deck, pitch-style slides | Full template workflow below |
| **Single-page report** | Eval matrix, dashboard, comparison writeup, tree viewer shell | [reference-html-bar.md](reference-html-bar.md) + `frontend-design` principles |

You may borrow **one** template's cover visual system for a single-page hero.
**Never** mash layouts from multiple templates.

### A2. Slide deck — template workflow (mandatory sequence)

Do **not** skip clarifying or preview steps. Full rules: [reference-templates.md](reference-templates.md).

1. **Ask occasion + mood** (wait for answer before picking):
   > Two quick questions before I pick a template:
   > 1. What's the occasion? (e.g. research synthesis, tech share, founder pitch)
   > 2. What mood / vibe? (e.g. confident & punchy, quiet & literary, dark & moody)

2. **Read** `$TEMPLATES/index.json` → pick **3** candidates that fit `mood` / `tone` / `best_for` / `formality`. Make them *different enough* (not three near-identical editorials).

3. **Title-slide previews** — for each candidate, clone sibling assets, keep only the cover slide, fill with the user's real title/subtitle/author/date. Save under e.g. `previews/01-<slug>.html`.

4. **Show paths to the user** and wait for a pick. On macOS use `open <path>`; on Linux/AutoDL open with available browser tools if present, otherwise print absolute paths clearly.

5. **Build the full deck** — clone the chosen template folder into the workspace; preserve design system; replace content; extend missing layouts *inside* that system only (see reference-templates).

6. **Deliver** absolute path to the final HTML (+ one-line tone rationale and any caveats).

### A3. Single-page — visual bar (mandatory)

Reports are **share artifacts**, not debug dumps. Meet this bar:

| Rule | Do | Don't |
|------|----|--------|
| First viewport | Title/brand, one headline, one short blurb, primary content cue | Dense tables, raw logs, path dumps as the hero |
| Typography | Distinct display + body fonts (Google Fonts or self-hosted) | Default `system-ui` / Inter / Arial only |
| Atmosphere | Subtle gradient, paper texture, or soft tonal field | Flat `#f8fafc` + blue chips only |
| Layout | One job per section; generous whitespace | Dashboard chrome, pill clusters, competing panels |
| Color | One clear palette (CSS variables) | Purple-on-white AI cliché; random chip rainbow |
| Data | Tables/charts **below** the fold or behind clear nav | Dumping full JSON / absolute host paths in UI |
| Mobile | Readable on phone | Horizontal-only dense matrices without scroll strategy |
| Motion | Optional 2–3 subtle transitions | Decorative noise |

Empty / failed states must be **first-class UI** (clear “no route / failed / pending”), not truncated `error_message` path strings.

Ship as a **directory**: `index.html`, `assets/*`, optional `data.json`. No secrets in the tree.

Starter CSS/HTML: [reference-html-bar.md](reference-html-bar.md).

---

## B) Publish

### B1. Serve: auth + read-only

- Serve **only** the report / deck directory.
- **HTTP Basic Auth** required for any non-localhost bind.
- Block dotfiles (`.env`, `.viewer_auth.json`, `.git`).
- Prefer a small dedicated static server (e.g. project `serve_*_viewer.py`) over `python -m http.server` on `0.0.0.0`.
- Credentials file **gitignored**; rotate by deleting and restarting.

Local preview only:

```bash
python -m http.server 8765 --bind 127.0.0.1
```

### B2. Expose: day-stable (preferred on EC2 / fixed IP)

```
Internet → <PUBLIC_IP>:80 (nginx) → 127.0.0.1:<PORT> (auth static server)
```

**Do not** use `cloudflared tunnel --url` / `*.trycloudflare.com` as the team bookmark — URL changes on restart.

Checklist:

1. nginx site proxies `/` → local auth server (see [reference-expose.md](reference-expose.md))
2. SG: TCP **80** (prefer office/VPN CIDR; if `0.0.0.0/0`, auth is mandatory and still weak alone)
3. Do **not** open databases, MinIO, model APIs, Redis, GPU services “for sharing”
4. Write `PUBLIC_URL.txt` next to the report
5. `curl -u USER:PASS http://<PUBLIC_IP>/` returns 200

HTTPS: add cert on nginx or a **named** tunnel with a stable hostname — still not random trycloudflare.

**AutoDL alternate:** no fixed team IP — use skill `static-html-report-serve` (port 6006). That path is typically **unauthenticated**; keep `--dir` minimal. Details in [reference-expose.md](reference-expose.md).

### B3. Security (never / always)

**Never**

- Expose repo root, `.env`, weights, object storage, or internal APIs
- Public bind without Basic Auth (except documented AutoDL 6006 tradeoff)
- Commit credentials or put passwords in tracked markdown
- Document only a trycloudflare URL after a fixed-IP path exists

**Always**

- Auth on the report process when using nginx/public IP
- Proxy only the report port
- Share URL + password privately; rotate after wide distribution
- Keep report content free of secrets (tokens, private SMILES policies as required by team)

---

## Agent checklist (copy)

```
Public HTML report:
Author
- [ ] Path chosen: slide deck (templates) OR single-page (visual bar)
- [ ] If deck: asked occasion/mood; 3 previews; user picked; design system preserved
- [ ] Visual bar / empty states; no secrets or absolute internal paths in UI
Publish
- [ ] Auth static server on loopback port (or AutoDL serve skill with minimal dir)
- [ ] nginx :80 → that port (EC2) OR static-html-report-serve (AutoDL)
- [ ] SG allows 80 when using public IP (scoped if possible)
- [ ] PUBLIC_URL.txt updated
- [ ] curl -u … → 200 (or AutoDL URL smoke-tested)
- [ ] Credentials shared out-of-band (when auth applies)
```

## Retro / domain adapters

If the report is retrosynthesis-specific, also follow project skill `retro-synth-viewer` for route JSON → tree/SVG. **Publish steps still follow this skill.**

For narrative structure of tech shares, `technical-narrative-deck` can inform content outline; **visual system** still comes from the template library or visual bar.

## Related

| Resource | Role |
|----------|------|
| `/root/autodl-tmp/taoyuzhou/beautiful-html-templates` (+ `AGENTS.md`) | External slide template library |
| `frontend-design` | Anti–AI-slop aesthetics for hand-authored UI |
| `static-html-report-serve` | AutoDL 自定义服务 6006 expose |
| `theme-factory` | Optional color/font themes for non-template artifacts |
| `retro-synth-viewer` | Domain adapter for retrosynthesis trees |

## Additional resources

- [reference-templates.md](reference-templates.md) — condensed template workflow
- [reference-html-bar.md](reference-html-bar.md) — single-page HTML/CSS patterns
- [reference-expose.md](reference-expose.md) — nginx + SG + AutoDL alternate
