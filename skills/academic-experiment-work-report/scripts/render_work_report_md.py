#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "templates" / "work_report_template.md"


def clean_text(value: object) -> str:
    return "" if value is None else str(value)


def strip_simple_html(text: str) -> str:
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.I)
    text = re.sub(r"</\s*p\s*>", "\n\n", text, flags=re.I)
    text = re.sub(r"<\s*p[^>]*>", "", text, flags=re.I)
    text = re.sub(r"<\s*strong[^>]*>(.*?)</\s*strong\s*>", r"**\1**", text, flags=re.I | re.S)
    text = re.sub(r"<\s*b[^>]*>(.*?)</\s*b\s*>", r"**\1**", text, flags=re.I | re.S)
    text = re.sub(r"<\s*em[^>]*>(.*?)</\s*em\s*>", r"*\1*", text, flags=re.I | re.S)
    text = re.sub(r"<\s*code[^>]*>(.*?)</\s*code\s*>", r"`\1`", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def md_table(table: dict) -> str:
    columns = table.get("columns")
    rows = table.get("rows", [])
    if not columns and rows:
        columns = list(rows[0].keys())
    columns = columns or []
    if not columns:
        return ""
    out = []
    out.append("| " + " | ".join(str(col) for col in columns) + " |")
    out.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        values = []
        for col in columns:
            text = clean_text(row.get(col, "")).replace("|", "\\|").replace("\n", "<br>")
            values.append(text)
        out.append("| " + " | ".join(values) + " |")
    return "\n".join(out)


def render_cards(cards: list[dict]) -> str:
    if not cards:
        return ""
    lines = ["## 快速指标", ""]
    for card in cards:
        lines.append(f"- **{clean_text(card.get('label', ''))}**: {clean_text(card.get('value', ''))}")
    return "\n".join(lines)


def render_figures(figures: list[dict]) -> str:
    chunks = []
    for fig in figures:
        src = clean_text(fig.get("src", ""))
        caption = clean_text(fig.get("caption", src))
        chunks.append(f"![{caption}]({src})")
    return "\n\n".join(chunks)


def render_sections(sections: list[dict]) -> str:
    chunks = []
    for idx, section in enumerate(sections, start=1):
        title = clean_text(section.get("title", f"Section {idx}"))
        body = clean_text(section.get("markdown", "")).strip()
        if not body and section.get("html"):
            body = strip_simple_html(clean_text(section.get("html", "")))
        figures = render_figures(section.get("figures", []))
        tables = "\n\n".join(md_table(table) for table in section.get("tables", []))
        parts = [f"## {idx}. {title}"]
        for item in [body, figures, tables]:
            if item:
                parts.extend(["", item])
        chunks.append("\n".join(parts))
    return "\n\n".join(chunks)


def render_sources(sources: list[object]) -> str:
    if not sources:
        return "_No sources listed._"
    lines = []
    for source in sources:
        if isinstance(source, dict):
            label = clean_text(source.get("label") or source.get("path") or source.get("href") or "source")
            href = source.get("href")
            path = source.get("path")
            if href:
                lines.append(f"- [{label}]({href})")
            elif path:
                lines.append(f"- `{path}`")
            else:
                lines.append(f"- {label}")
        else:
            lines.append(f"- `{source}`")
    return "\n".join(lines)


def replace_tokens(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def render_markdown(payload: dict, template_path: Path) -> str:
    template = template_path.read_text(encoding="utf-8")
    text = replace_tokens(
        template,
        {
            "TITLE": clean_text(payload.get("title", "Academic Experiment Work Report")),
            "SUBTITLE": clean_text(payload.get("subtitle", "")),
            "CARDS": render_cards(payload.get("cards", [])),
            "SECTIONS": render_sections(payload.get("sections", [])),
            "SOURCES": render_sources(payload.get("sources", [])),
        },
    )
    text = re.sub(r"\n{4,}", "\n\n\n", text).rstrip() + "\n"
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Markdown academic experiment work report from JSON.")
    parser.add_argument("--payload", required=True, type=Path, help="JSON payload path.")
    parser.add_argument("--out-md", required=True, type=Path, help="Output Markdown path.")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="Markdown template path.")
    args = parser.parse_args()

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_markdown(payload, args.template), encoding="utf-8")
    print(args.out_md)


if __name__ == "__main__":
    main()
