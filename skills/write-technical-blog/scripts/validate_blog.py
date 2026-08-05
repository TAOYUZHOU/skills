#!/usr/bin/env python3
"""Structural checks for a standalone technical-blog HTML file."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class BlogParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.counts: dict[str, int] = {}
        self.images: list[str] = []
        self.heading_text: list[str] = []
        self._heading: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.counts[tag] = self.counts.get(tag, 0) + 1
        values = dict(attrs)
        if tag == "img" and values.get("src"):
            self.images.append(values["src"] or "")
        if tag in {"h1", "h2", "h3"}:
            self._heading = ""
        if tag not in VOID:
            self.stack.append(tag)

    def handle_data(self, data: str) -> None:
        if self._heading is not None:
            self._heading += data

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3"} and self._heading is not None:
            self.heading_text.append(" ".join(self._heading.split()))
            self._heading = None
        if tag not in self.stack:
            self.errors.append(f"unexpected closing tag </{tag}>")
            return
        while self.stack:
            opened = self.stack.pop()
            if opened == tag:
                return
            self.errors.append(f"unclosed <{opened}> before </{tag}>")


def validate(path: Path, strict: bool) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    parser = BlogParser()
    parser.feed(text)
    errors = list(parser.errors)
    warnings: list[str] = []
    if parser.stack:
        errors.append("unclosed tags: " + ", ".join(parser.stack))
    if re.search(r"\{\{[^{}]+\}\}", text):
        errors.append("unreplaced {{...}} template tokens remain")
    for required in ("title", "h1", "section"):
        if parser.counts.get(required, 0) == 0:
            errors.append(f"missing required <{required}> element")
    if parser.counts.get("table", 0) == 0:
        warnings.append("no table found; consider a notation or parameter table")
    if "\\[" in text and "mathjax" not in text.lower():
        errors.append("display math found but MathJax was not loaded")
    for src in parser.images:
        if re.match(r"^(?:https?:|data:)", src):
            warnings.append(f"external/embedded image is not a local relative asset: {src}")
        elif src.startswith("/"):
            warnings.append(f"absolute image path is not portable: {src}")
        elif not (path.parent / src).exists():
            errors.append(f"missing image: {src}")
    vague = {"overview", "introduction", "results", "discussion", "总结", "介绍", "结果"}
    for heading in parser.heading_text:
        if heading.strip().lower() in vague:
            warnings.append(f"generic heading could state a claim: {heading!r}")
    if strict and warnings:
        errors.extend("strict: " + item for item in warnings)
    return errors, warnings


def main() -> int:
    argp = argparse.ArgumentParser()
    argp.add_argument("html", type=Path)
    argp.add_argument("--strict", action="store_true")
    args = argp.parse_args()
    if not args.html.is_file():
        print(f"ERROR: file not found: {args.html}")
        return 2
    errors, warnings = validate(args.html.resolve(), args.strict)
    for item in warnings:
        print(f"WARNING: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    if errors:
        return 1
    print(f"OK: {args.html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
