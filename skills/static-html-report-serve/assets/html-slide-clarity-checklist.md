# HTML slide clarity checklist (before publishing)

Use with **1920×1080 fixed canvas + scale-to-fit** (never raw `vw`/`vh` for slide content).

## Layout rules

1. **Primary visual first** — flowchart / architecture / GIF must be the largest element on the slide.
2. **Target fill** — main visual ≥ **52%** of slide height on 1440×900; overall content ≥ **85%**.
3. **Dense slides** — use `.slide.dense` + `.slide-head` (compact title) + `.slide-main` (flex:1).
4. **Flowcharts** — `.svg-wrap.flowchart` with `svg { width:100%; height:100% }`, min-height ≥ 420px in design space.
5. **Call chains** — use `.flow-block` at 14px+, flex:1 (not `.flow-mini` capped at 300px).
6. **Split if crowded** — if text + diagram cannot both be readable, add a slide instead of shrinking the diagram.
7. **Side notes** — put bullets in `.info-stack` beside chart (not below a tiny chart).

## Verification

```bash
SKILL=skills/static-html-report-serve
python3 report/_layout_probe.py dense_v2 2   # flowchart slide metrics + screenshot
python3 "$SKILL/scripts/check_slide_density.py" report/retro_engine_work_report_slides.html
```

## Information completeness

- Every slide answers one question; no orphan bullets without context.
- Acronyms defined once (RMT, FMT, BBL, mssr, mrp).
- Evidence slides cite artifact filenames and numeric smoke results.
- Roadmap slides tie actions to Tier-1/2/3 gates.
