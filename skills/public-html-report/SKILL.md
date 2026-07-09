---
name: public-html-report
description: >-
  Turn any task report into a beautiful, day-stable, publicly reachable static
  HTML site with HTTP Basic Auth, nginx reverse proxy on a fixed public IP
  (not trycloudflare), and strict expose-only-the-report security. Use when
  sharing eval results, experiment writeups, comparison matrices, dashboards,
  or any HTML report with teammates; also when the user asks for a public URL,
  fixed IP, reverse proxy, or to publish a report.
---

# Public HTML Report

Generic skill for **any domain**: build a self-contained static HTML report, serve it read-only with auth, expose via **fixed public IP + nginx** for day-level stable links.

Domain-specific content (e.g. retrosynthesis trees) lives in separate skills; **this skill owns publish + security + visual bar**.

## When to use

- User wants a report / HTML / comparison page **visible on the public internet**
- “给个链接给同事看”、day-stable URL、固定公网 IP、反向代理
- Replacing ephemeral `*.trycloudflare.com` tunnels

## Pipeline

```
1. Author   → self-contained static site (index.html + assets; no server-side code)
2. Serve    → read-only HTTP + Basic Auth (bind 127.0.0.1 or behind nginx only)
3. Expose   → nginx :80 → auth backend; SG allows 80 (optional app port)
4. Document → PUBLIC_URL.txt with URL; share credentials out-of-band
5. Verify   → curl -u USER:PASS http://<PUBLIC_IP>/ → 200
```

## 1) Author: visual bar (mandatory)

Reports are **share artifacts**, not internal debug dumps. Meet this bar:

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

## 2) Serve: auth + read-only

- Serve **only** the report directory.
- **HTTP Basic Auth** required for any non-localhost bind.
- Block dotfiles (`.env`, `.viewer_auth.json`, `.git`).
- Prefer a small dedicated static server (e.g. project `serve_*_viewer.py`) over `python -m http.server` on `0.0.0.0`.
- Credentials file **gitignored**; rotate by deleting and restarting.

Local preview only:

```bash
python -m http.server 8765 --bind 127.0.0.1
```

## 3) Expose: day-stable (preferred)

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

## 4) Security (never / always)

**Never**

- Expose repo root, `.env`, weights, object storage, or internal APIs
- Public bind without Basic Auth
- Commit credentials or put passwords in tracked markdown
- Document only a trycloudflare URL after a fixed-IP path exists

**Always**

- Auth on the report process
- Proxy only the report port
- Share URL + password privately; rotate after wide distribution
- Keep report content free of secrets (tokens, private SMILES policies as required by team)

## 5) Agent checklist (copy)

```
Public HTML report:
- [ ] Static site meets visual bar (hero, fonts, atmosphere, empty states)
- [ ] No secrets / absolute internal paths in visible UI
- [ ] Auth static server on loopback port
- [ ] nginx :80 → that port
- [ ] SG allows 80 (scoped if possible)
- [ ] PUBLIC_URL.txt updated
- [ ] curl -u … http://<PUBLIC_IP>/ → 200
- [ ] Credentials shared out-of-band
```

## Retro / domain adapters

If the report is retrosynthesis-specific, also follow project skill `retro-synth-viewer` for route JSON → tree/SVG. **Publish steps still follow this skill.**

## Additional resources

- [reference-expose.md](reference-expose.md) — nginx + SG commands
- [reference-html-bar.md](reference-html-bar.md) — HTML/CSS starter patterns
