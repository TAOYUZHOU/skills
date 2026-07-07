#!/usr/bin/env python3
"""Verify HTML slides meet minimum visual density (Playwright).

Fails if primary visual (svg/img/flow-block) occupies too little of the slide canvas.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

JS = """
(args) => {
  const slideIndex = args.slideIndex;
  const minVisual = args.minVisual;
  const slides = [...document.querySelectorAll('.slide')];
  slides.forEach((s, j) => s.classList.toggle('active', j === slideIndex));
  const slide = slides[slideIndex];
  const sh = slide.getBoundingClientRect();
  const visual = slide.querySelector(
    '.svg-wrap.flowchart svg, .svg-wrap.panel-chart svg, .flow-block, .img-wrap.hero img'
  );
  const vh = visual ? visual.getBoundingClientRect().height : 0;
  const ratio = sh.height ? vh / sh.height : 0;
  return {
    slideIndex,
    slideHeight: Math.round(sh.height),
    visualHeight: Math.round(vh),
    visualFillRatio: Math.round(ratio * 1000) / 1000,
    pass: ratio >= minVisual,
    selector: visual ? visual.tagName.toLowerCase() : null,
  };
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Check HTML slide visual density")
    ap.add_argument("html", type=Path, help="Path or file:// URL to slides HTML")
    ap.add_argument(
        "--slides",
        default="2,6,7,8",
        help="Comma-separated slide indices to check (0-based)",
    )
    ap.add_argument("--min-visual", type=float, default=0.52, help="Min visual/slide height ratio")
    args = ap.parse_args()

    url = args.html.as_uri() if args.html.exists() else str(args.html)
    indices = [int(x.strip()) for x in args.slides.split(",") if x.strip()]

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(400)
        for idx in indices:
            r = page.evaluate(JS, {"slideIndex": idx, "minVisual": args.min_visual})
            results.append(r)
        browser.close()

    failed = [r for r in results if not r["pass"]]
    print(json.dumps({"results": results, "pass": not failed}, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
