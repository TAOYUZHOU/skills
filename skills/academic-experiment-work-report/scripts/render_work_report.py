#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "templates" / "work_report_template.html"


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def render_cards(cards: list[dict]) -> str:
    if not cards:
        return ""
    return "\n".join(
        f'<div class="metric"><div class="k">{esc(card.get("label", ""))}</div>'
        f'<div class="v">{esc(card.get("value", ""))}</div></div>'
        for card in cards
    )


def render_table(table: dict) -> str:
    columns = table.get("columns")
    rows = table.get("rows", [])
    if not columns and rows:
        columns = list(rows[0].keys())
    columns = columns or []
    head = "<thead><tr>" + "".join(f"<th>{esc(col)}</th>" for col in columns) + "</tr></thead>"
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join(f"<td>{esc(row.get(col, ''))}</td>" for col in columns) + "</tr>")
    return "<table>" + head + "<tbody>" + "\n".join(body_rows) + "</tbody></table>"


def render_figures(figures: list[dict]) -> str:
    if not figures:
        return ""
    chunks = []
    for fig in figures:
        chunks.append(
            "<figure>"
            f'<img src="{esc(fig.get("src", ""))}" alt="{esc(fig.get("caption", ""))}">'
            f"<figcaption>{esc(fig.get('caption', ''))}</figcaption>"
            "</figure>"
        )
    if len(chunks) == 2:
        return '<div class="figgrid">' + "\n".join(chunks) + "</div>"
    return "\n".join(chunks)


def render_sections(sections: list[dict]) -> str:
    out = []
    for section in sections:
        title = section.get("title", "")
        body = section.get("html", "")
        figures = render_figures(section.get("figures", []))
        tables = "\n".join(render_table(table) for table in section.get("tables", []))
        out.append(f"<section><h2>{esc(title)}</h2>\n{body}\n{figures}\n{tables}\n</section>")
    return "\n".join(out)


def render_sources(sources: list[object]) -> str:
    if not sources:
        return '<p class="footer">No sources listed.</p>'
    items = []
    for source in sources:
        if isinstance(source, dict):
            label = source.get("label") or source.get("path") or source.get("href") or "source"
            href = source.get("href")
            path = source.get("path")
            text = esc(label)
            if href:
                text = f'<a href="{esc(href)}">{text}</a>'
            elif path:
                text = f"<code>{esc(path)}</code>"
            items.append(f"<li>{text}</li>")
        else:
            items.append(f"<li><code>{esc(source)}</code></li>")
    return "<ul>" + "\n".join(items) + "</ul>"


def replace_tokens(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def render_html(payload: dict, template_path: Path) -> str:
    template = template_path.read_text(encoding="utf-8")
    return replace_tokens(
        template,
        {
            "TITLE": esc(payload.get("title", "Academic Experiment Work Report")),
            "SUBTITLE": esc(payload.get("subtitle", "")),
            "CARDS": render_cards(payload.get("cards", [])),
            "SECTIONS": render_sections(payload.get("sections", [])),
            "SOURCES": render_sources(payload.get("sources", [])),
        },
    )


def export_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise SystemExit("No Chrome/Chromium binary found for PDF export.")
    subprocess.run(
        [
            chrome,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri(),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Chinese academic experiment work report from JSON.")
    parser.add_argument("--payload", required=True, type=Path, help="JSON payload path.")
    parser.add_argument("--out-html", required=True, type=Path, help="Output HTML path.")
    parser.add_argument("--out-pdf", type=Path, help="Optional output PDF path via Chrome headless.")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="HTML template path.")
    args = parser.parse_args()

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    args.out_html.parent.mkdir(parents=True, exist_ok=True)
    args.out_html.write_text(render_html(payload, args.template), encoding="utf-8")
    print(args.out_html)
    if args.out_pdf:
        args.out_pdf.parent.mkdir(parents=True, exist_ok=True)
        export_pdf(args.out_html, args.out_pdf)
        print(args.out_pdf)


if __name__ == "__main__":
    main()
