#!/usr/bin/env python3
"""Render an honest agent-work path tree as one standalone HTML file."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


STATUSES = {"done", "in_progress", "pending", "blocked"}
STATUS_LABELS = {
    "done": "已完成",
    "in_progress": "进行中",
    "pending": "待开始",
    "blocked": "受阻",
}


def fail(message: str) -> None:
    raise ValueError(message)


def require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{path} must be an object")
    return value


def require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{path} must be an array")
    return value


def require_text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{path} must be a non-empty string")
    return value.strip()


def optional_text(value: Any, path: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        fail(f"{path} must be a string")
    return value.strip()


def text_list(value: Any, path: str) -> list[str]:
    if value is None:
        return []
    rows = require_list(value, path)
    return [require_text(item, f"{path}[{index}]") for index, item in enumerate(rows)]


def validate_link(value: Any, path: str) -> dict[str, str]:
    row = require_dict(value, path)
    label = require_text(row.get("label"), f"{path}.label")
    target = require_text(row.get("path"), f"{path}.path")
    parsed = urlparse(target)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        fail(f"{path}.path uses unsupported URL scheme: {parsed.scheme}")
    if target.lower().lstrip().startswith(("javascript:", "data:")):
        fail(f"{path}.path is unsafe")
    return {
        "label": label,
        "path": target,
        "note": optional_text(row.get("note"), f"{path}.note"),
    }


def validate_payload(raw: Any) -> dict[str, Any]:
    root = require_dict(raw, "payload")
    if root.get("schema_version") != 1:
        fail("payload.schema_version must equal 1")
    title = require_text(root.get("title"), "payload.title")
    summary = require_dict(root.get("summary"), "payload.summary")
    summary_status = require_text(summary.get("status"), "payload.summary.status")
    if summary_status not in STATUSES:
        fail(f"payload.summary.status must be one of {sorted(STATUSES)}")
    headline = require_text(summary.get("headline"), "payload.summary.headline")

    metrics: list[dict[str, str]] = []
    for index, value in enumerate(require_list(summary.get("metrics", []), "payload.summary.metrics")):
        row = require_dict(value, f"payload.summary.metrics[{index}]")
        metrics.append(
            {
                "value": require_text(row.get("value"), f"payload.summary.metrics[{index}].value"),
                "label": require_text(row.get("label"), f"payload.summary.metrics[{index}].label"),
                "detail": optional_text(row.get("detail"), f"payload.summary.metrics[{index}].detail"),
            }
        )

    phases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, value in enumerate(require_list(root.get("phases"), "payload.phases")):
        row = require_dict(value, f"payload.phases[{index}]")
        raw_id = row.get("id")
        if not isinstance(raw_id, (str, int)) or isinstance(raw_id, bool):
            fail(f"payload.phases[{index}].id must be a string or integer")
        phase_id = str(raw_id).strip()
        if not phase_id or phase_id in seen_ids:
            fail(f"payload.phases[{index}].id must be non-empty and unique")
        seen_ids.add(phase_id)
        status = require_text(row.get("status"), f"payload.phases[{index}].status")
        if status not in STATUSES:
            fail(f"payload.phases[{index}].status must be one of {sorted(STATUSES)}")
        evidence = [
            validate_link(item, f"payload.phases[{index}].evidence[{link_index}]")
            for link_index, item in enumerate(
                require_list(row.get("evidence", []), f"payload.phases[{index}].evidence")
            )
        ]
        phases.append(
            {
                "id": phase_id,
                "display_id": f"{int(phase_id):02d}" if phase_id.isdigit() else phase_id,
                "label": require_text(row.get("label"), f"payload.phases[{index}].label"),
                "status": status,
                "purpose": require_text(row.get("purpose"), f"payload.phases[{index}].purpose"),
                "outcome": require_text(row.get("outcome"), f"payload.phases[{index}].outcome"),
                "work": text_list(row.get("work"), f"payload.phases[{index}].work"),
                "solved": text_list(row.get("solved"), f"payload.phases[{index}].solved"),
                "achievements": text_list(row.get("achievements"), f"payload.phases[{index}].achievements"),
                "caveats": text_list(row.get("caveats"), f"payload.phases[{index}].caveats"),
                "evidence": evidence,
            }
        )
    if not phases:
        fail("payload.phases must not be empty")

    principles: list[dict[str, str]] = []
    for index, value in enumerate(require_list(root.get("principles", []), "payload.principles")):
        row = require_dict(value, f"payload.principles[{index}]")
        principles.append(
            {
                "title": require_text(row.get("title"), f"payload.principles[{index}].title"),
                "body": require_text(row.get("body"), f"payload.principles[{index}].body"),
            }
        )

    current = require_dict(root.get("current_state", {}), "payload.current_state")
    sources = [
        validate_link(item, f"payload.sources[{index}]")
        for index, item in enumerate(require_list(root.get("sources", []), "payload.sources"))
    ]
    return {
        "lang": optional_text(root.get("lang"), "payload.lang") or "zh-CN",
        "eyebrow": optional_text(root.get("eyebrow"), "payload.eyebrow") or "AGENT WORK / EVIDENCE MAP",
        "title": title,
        "subtitle": optional_text(root.get("subtitle"), "payload.subtitle"),
        "updated_at": optional_text(root.get("updated_at"), "payload.updated_at"),
        "summary": {
            "status": summary_status,
            "headline": headline,
            "narrative": optional_text(summary.get("narrative"), "payload.summary.narrative"),
            "metrics": metrics,
        },
        "phases": phases,
        "principles": principles,
        "current_state": {
            "headline": optional_text(current.get("headline"), "payload.current_state.headline")
            or "Current truth",
            "facts": text_list(current.get("facts"), "payload.current_state.facts"),
            "open_gaps": text_list(current.get("open_gaps"), "payload.current_state.open_gaps"),
            "next_steps": text_list(current.get("next_steps"), "payload.current_state.next_steps"),
        },
        "sources": sources,
    }


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_list(items: list[str], css_class: str = "") -> str:
    if not items:
        return '<p class="empty">没有单独记录。</p>'
    cls = f' class="{esc(css_class)}"' if css_class else ""
    return f"<ul{cls}>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def render_links(items: list[dict[str, str]]) -> str:
    if not items:
        return '<p class="empty">本卡片未列独立证据链接。</p>'
    rows = []
    for item in items:
        note = f'<span>{esc(item["note"])}</span>' if item["note"] else ""
        rows.append(
            f'<li><a href="{esc(item["path"])}">{esc(item["label"])}</a>{note}</li>'
        )
    return '<ul class="evidence-list">' + "".join(rows) + "</ul>"


def render_phase(phase: dict[str, Any]) -> str:
    status = phase["status"]
    return f"""
    <article class="phase phase--{esc(status)}" id="phase-{esc(phase['id'])}" data-status="{esc(status)}">
      <div class="phase-node" aria-hidden="true"><span>{esc(phase['display_id'])}</span></div>
      <div class="phase-card">
        <header class="phase-head">
          <div>
            <p class="phase-kicker">PHASE {esc(phase['display_id'])}</p>
            <h2>{esc(phase['label'])}</h2>
          </div>
          <span class="status status--{esc(status)}">{esc(STATUS_LABELS[status])}</span>
        </header>
        <p class="purpose">{esc(phase['purpose'])}</p>
        <p class="outcome">{esc(phase['outcome'])}</p>
        <div class="phase-grid">
          <section><h3><span>01</span> 做了什么</h3>{render_list(phase['work'])}</section>
          <section><h3><span>02</span> 解决什么</h3>{render_list(phase['solved'])}</section>
          <section><h3><span>03</span> 获得什么</h3>{render_list(phase['achievements'], 'achievement-list')}</section>
          <section class="limits"><h3><span>04</span> 边界 / 未完成</h3>{render_list(phase['caveats'], 'caveat-list')}</section>
        </div>
        <details class="evidence">
          <summary>查看证据索引 <span>{len(phase['evidence'])} 项</span></summary>
          {render_links(phase['evidence'])}
        </details>
      </div>
    </article>
    """.strip()


def render(payload: dict[str, Any], source_name: str) -> str:
    summary = payload["summary"]
    phases = payload["phases"]
    counts = {status: sum(1 for phase in phases if phase["status"] == status) for status in STATUSES}
    metrics = "".join(
        f'<div class="metric"><strong>{esc(item["value"])}</strong><span>{esc(item["label"])}</span>'
        f'<small>{esc(item["detail"])}</small></div>'
        for item in summary["metrics"]
    )
    principles = "".join(
        f'<article><h3>{esc(item["title"])}</h3><p>{esc(item["body"])}</p></article>'
        for item in payload["principles"]
    )
    rail = "".join(
        f'<a href="#phase-{esc(phase["id"])}" class="rail-item rail-item--{esc(phase["status"])}">'
        f'<span>{esc(phase["display_id"])}</span><small>{esc(phase["label"])}</small></a>'
        for phase in phases
    )
    phase_html = "".join(render_phase(phase) for phase in phases)
    source_html = render_links(payload["sources"])
    current = payload["current_state"]
    generated_note = " · ".join(
        part for part in [f"数据：{source_name}", f"更新：{payload['updated_at']}" if payload["updated_at"] else ""] if part
    )

    return f"""<!doctype html>
<html lang="{esc(payload['lang'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>{esc(payload['title'])}</title>
  <style>
    :root {{
      --paper:#f3efe5; --paper-2:#fffdf7; --ink:#14211d; --muted:#65706a;
      --line:#c9c4b5; --forest:#1e5a46; --forest-soft:#dcebe3; --amber:#bd6a23;
      --amber-soft:#f5e4cf; --red:#a33b32; --red-soft:#f3dcd6; --slate:#66706f;
      --slate-soft:#e4e5e0; --shadow:0 18px 50px rgba(39,43,37,.09);
      --display:"Noto Serif SC","Songti SC","STSong",Georgia,serif;
      --body:"Noto Sans CJK SC","Microsoft YaHei","PingFang SC",sans-serif;
    }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; }}
    body {{ margin:0; color:var(--ink); background:
      radial-gradient(circle at 8% 4%,rgba(189,106,35,.11),transparent 24rem),
      linear-gradient(90deg,rgba(20,33,29,.025) 1px,transparent 1px),var(--paper);
      background-size:auto,42px 42px,auto; font-family:var(--body); line-height:1.68; }}
    a {{ color:var(--forest); text-decoration-thickness:1px; text-underline-offset:3px; }}
    h1,h2,h3,p,li {{ overflow-wrap:anywhere; }}
    a:focus-visible,button:focus-visible,summary:focus-visible {{ outline:3px solid rgba(189,106,35,.45); outline-offset:3px; }}
    .wrap {{ width:min(1180px,calc(100% - 40px)); margin:0 auto; }}
    .hero {{ min-height:78vh; padding:72px 0 46px; display:grid; align-items:center; border-bottom:1px solid var(--line); }}
    .eyebrow,.phase-kicker {{ margin:0 0 12px; letter-spacing:.18em; font-size:.73rem; font-weight:800; color:var(--amber); }}
    h1 {{ margin:0; max-width:980px; font:700 clamp(3rem,8vw,7.4rem)/.96 var(--display); letter-spacing:-.055em; }}
    .subtitle {{ max-width:770px; margin:28px 0 0; color:var(--muted); font-size:1rem; }}
    .truth {{ margin-top:46px; display:grid; grid-template-columns:minmax(0,1.5fr) minmax(250px,.5fr); gap:28px; align-items:end; }}
    .truth-copy {{ min-width:0; border-left:5px solid var(--forest); padding:4px 0 4px 24px; }}
    .truth-copy h2 {{ margin:8px 0 10px; font:700 clamp(1.6rem,3vw,2.65rem)/1.16 var(--display); }}
    .truth-copy p {{ margin:0; max-width:780px; color:var(--muted); }}
    .status {{ display:inline-flex; align-items:center; gap:8px; padding:5px 10px; border:1px solid currentColor; border-radius:2px; font-size:.72rem; font-weight:800; letter-spacing:.08em; white-space:nowrap; }}
    .status::before {{ content:""; width:7px; height:7px; border-radius:50%; background:currentColor; }}
    .status--done {{ color:var(--forest); background:var(--forest-soft); }}
    .status--in_progress {{ color:var(--amber); background:var(--amber-soft); }}
    .status--pending {{ color:var(--slate); background:var(--slate-soft); }}
    .status--blocked {{ color:var(--red); background:var(--red-soft); }}
    .count-strip {{ display:grid; grid-template-columns:repeat(4,1fr); border:1px solid var(--line); background:rgba(255,253,247,.6); }}
    .count-strip div {{ padding:14px 12px; border-right:1px solid var(--line); text-align:center; }}
    .count-strip div:last-child {{ border-right:0; }}
    .count-strip strong {{ display:block; font:700 1.55rem var(--display); }}
    .count-strip span {{ color:var(--muted); font-size:.68rem; }}
    .metrics {{ padding:42px 0; display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:1px; background:var(--line); border:1px solid var(--line); }}
    .metric {{ min-height:145px; padding:22px; background:var(--paper-2); display:flex; flex-direction:column; }}
    .metric strong {{ font:700 2.6rem/1 var(--display); color:var(--forest); }}
    .metric span {{ margin-top:12px; font-weight:800; }}
    .metric small {{ margin-top:auto; padding-top:12px; color:var(--muted); }}
    .principles-section {{ padding:78px 0; }}
    .section-label {{ margin:0 0 26px; font:700 clamp(1.8rem,4vw,3.4rem)/1.05 var(--display); }}
    .principles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:18px; }}
    .principles article {{ padding:22px 22px 26px; border-top:3px solid var(--forest); background:rgba(255,253,247,.56); }}
    .principles h3 {{ margin:0 0 8px; font:700 1.15rem var(--display); }}
    .principles p {{ margin:0; color:var(--muted); font-size:.92rem; }}
    .path-rail {{ position:sticky; top:0; z-index:10; padding:12px max(20px,calc((100% - 1180px)/2)); display:flex; overflow:auto; gap:4px; background:rgba(20,33,29,.96); box-shadow:0 10px 28px rgba(20,33,29,.16); }}
    .rail-item {{ min-width:104px; flex:1; color:#f7f1e6; text-decoration:none; padding:8px 10px; border-bottom:3px solid #53635d; }}
    .rail-item span {{ display:block; font:700 1rem var(--display); }}
    .rail-item small {{ display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; opacity:.72; font-size:.65rem; }}
    .rail-item--done {{ border-color:#72b58f; }} .rail-item--in_progress {{ border-color:#e5a35c; }}
    .rail-item--blocked {{ border-color:#dc7469; }}
    .filters {{ display:flex; flex-wrap:wrap; gap:8px; padding:48px 0 8px; }}
    .filters button {{ appearance:none; border:1px solid var(--line); background:var(--paper-2); color:var(--ink); padding:8px 12px; font:700 .78rem var(--body); cursor:pointer; }}
    .filters button[aria-pressed="true"] {{ color:#fff; background:var(--ink); border-color:var(--ink); }}
    .path {{ position:relative; padding:42px 0 110px; }}
    .path::before {{ content:""; position:absolute; left:45px; top:0; bottom:70px; width:2px; background:linear-gradient(var(--forest),var(--amber),var(--line)); }}
    .phase {{ position:relative; display:grid; grid-template-columns:92px minmax(0,1fr); margin:0 0 58px; scroll-margin-top:96px; }}
    .phase[hidden] {{ display:none; }}
    .phase-node {{ position:relative; z-index:2; width:68px; height:68px; border:2px solid var(--ink); background:var(--paper); display:grid; place-items:center; transform:rotate(45deg); box-shadow:7px 7px 0 var(--forest-soft); }}
    .phase-node span {{ transform:rotate(-45deg); font:700 1.4rem var(--display); }}
    .phase--in_progress .phase-node {{ box-shadow:7px 7px 0 var(--amber-soft); }}
    .phase--pending .phase-node {{ box-shadow:7px 7px 0 var(--slate-soft); }}
    .phase--blocked .phase-node {{ box-shadow:7px 7px 0 var(--red-soft); }}
    .phase-card {{ position:relative; min-width:0; border:1px solid var(--line); border-top:5px solid var(--forest); background:rgba(255,253,247,.93); box-shadow:var(--shadow); }}
    .phase-card::before {{ content:""; position:absolute; top:31px; left:-25px; width:24px; border-top:2px solid var(--line); }}
    .phase--in_progress .phase-card {{ border-top-color:var(--amber); }}
    .phase--pending .phase-card {{ border-top-color:var(--slate); }}
    .phase--blocked .phase-card {{ border-top-color:var(--red); }}
    .phase-head {{ padding:28px 30px 20px; display:flex; justify-content:space-between; gap:24px; align-items:flex-start; }}
    .phase-head > div {{ min-width:0; }}
    .phase-head h2 {{ margin:0; font:700 clamp(1.65rem,3vw,2.6rem)/1.08 var(--display); }}
    .purpose {{ margin:0; padding:0 30px 20px; color:var(--muted); }}
    .outcome {{ margin:0; padding:22px 30px; border-block:1px solid var(--line); background:rgba(220,235,227,.42); font:700 1.05rem/1.6 var(--display); }}
    .phase--in_progress .outcome {{ background:rgba(245,228,207,.5); }}
    .phase-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); }}
    .phase-grid section {{ padding:24px 30px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); }}
    .phase-grid section:nth-child(2n) {{ border-right:0; }}
    .phase-grid h3 {{ margin:0 0 12px; font:700 .92rem var(--body); letter-spacing:.04em; }}
    .phase-grid h3 span {{ color:var(--amber); margin-right:7px; }}
    ul {{ margin:0; padding-left:1.1rem; }} li+li {{ margin-top:8px; }}
    .achievement-list li::marker {{ color:var(--forest); }} .caveat-list li::marker {{ color:var(--red); }}
    .empty {{ margin:0; color:var(--muted); font-style:italic; }}
    .evidence {{ padding:17px 30px 22px; }}
    .evidence summary {{ cursor:pointer; font-weight:800; color:var(--forest); }}
    .evidence summary span {{ color:var(--muted); font-weight:400; }}
    .evidence-list {{ margin-top:16px; list-style:none; padding:0; display:grid; gap:9px; }}
    .evidence-list li {{ display:grid; grid-template-columns:minmax(150px,.34fr) 1fr; gap:18px; padding-top:9px; border-top:1px dotted var(--line); }}
    .evidence-list span {{ color:var(--muted); font-size:.86rem; }}
    .current {{ padding:76px 0; color:#f8f2e7; background:var(--ink); }}
    .current h2 {{ margin:0 0 34px; font:700 clamp(2rem,5vw,4.2rem)/1.03 var(--display); }}
    .current-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1px; background:#52605b; }}
    .current-grid section {{ padding:26px; background:#172923; }}
    .current-grid h3 {{ margin:0 0 15px; color:#e7aa65; font:700 1rem var(--body); }}
    .current-grid li::marker {{ color:#7ab390; }}
    .sources {{ padding:72px 0 96px; }}
    .sources .evidence-list {{ border-top:1px solid var(--line); }}
    footer {{ padding:20px; border-top:1px solid var(--line); color:var(--muted); text-align:center; font-size:.75rem; }}
    @media (max-width:760px) {{
      body {{ overflow-x:hidden; }}
      .wrap {{ width:auto; max-width:none; margin-inline:12px; }} .hero {{ min-height:auto; padding-top:48px; }}
      .hero h1 {{ max-width:100%; font-size:clamp(2.35rem,11.5vw,3.45rem); letter-spacing:0; word-break:break-all; }}
      .truth,.current-grid {{ grid-template-columns:1fr; }} .count-strip {{ grid-template-columns:repeat(2,1fr); }}
      .truth-copy h2 {{ font-size:clamp(1.45rem,7vw,2rem); }}
      .path::before {{ left:27px; }} .phase {{ grid-template-columns:60px minmax(0,1fr); }}
      .phase-node {{ width:46px; height:46px; }} .phase-node span {{ font-size:1rem; }}
      .phase-card::before {{ top:21px; left:-14px; width:13px; }}
      .phase-head {{ padding:22px 20px 16px; flex-direction:column; }} .purpose {{ padding:0 20px 18px; }}
      .outcome {{ padding:18px 20px; }} .phase-grid {{ grid-template-columns:1fr; }}
      .phase-grid section,.phase-grid section:nth-child(2n) {{ padding:20px; border-right:0; }}
      .evidence {{ padding:16px 20px; }} .evidence-list li {{ grid-template-columns:1fr; gap:2px; }}
    }}
    @media (prefers-reduced-motion:reduce) {{ html {{ scroll-behavior:auto; }} }}
    @media print {{
      body {{ background:#fff; }} .hero {{ min-height:auto; }} .path-rail,.filters {{ display:none; }}
      .phase {{ break-inside:avoid; }} .phase-card {{ box-shadow:none; }} details {{ open:true; }}
    }}
  </style>
</head>
<body>
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow">{esc(payload['eyebrow'])}</p>
      <h1>{esc(payload['title'])}</h1>
      <p class="subtitle">{esc(payload['subtitle'])}</p>
      <div class="truth">
        <div class="truth-copy">
          <span class="status status--{esc(summary['status'])}">{esc(STATUS_LABELS[summary['status']])}</span>
          <h2>{esc(summary['headline'])}</h2>
          <p>{esc(summary['narrative'])}</p>
        </div>
        <div class="count-strip" aria-label="阶段状态统计">
          <div><strong>{counts['done']}</strong><span>完成</span></div>
          <div><strong>{counts['in_progress']}</strong><span>进行中</span></div>
          <div><strong>{counts['pending']}</strong><span>待开始</span></div>
          <div><strong>{counts['blocked']}</strong><span>受阻</span></div>
        </div>
      </div>
    </div>
  </header>
  <section class="wrap metrics" aria-label="核心数字">{metrics}</section>
  <section class="wrap principles-section">
    <p class="eyebrow">DESIGN RULES</p><h2 class="section-label">贯穿九个阶段的边界</h2>
    <div class="principles">{principles}</div>
  </section>
  <nav class="path-rail" aria-label="Phase 路径">{rail}</nav>
  <main class="wrap">
    <div class="filters" aria-label="筛选阶段">
      <button type="button" data-filter="all" aria-pressed="true">全部</button>
      <button type="button" data-filter="done" aria-pressed="false">已完成</button>
      <button type="button" data-filter="in_progress" aria-pressed="false">进行中</button>
      <button type="button" data-filter="pending" aria-pressed="false">待开始</button>
      <button type="button" data-filter="blocked" aria-pressed="false">受阻</button>
    </div>
    <div class="path">{phase_html}</div>
  </main>
  <section class="current">
    <div class="wrap">
      <p class="eyebrow">NOW / NEXT</p><h2>{esc(current['headline'])}</h2>
      <div class="current-grid">
        <section><h3>现在可以确认</h3>{render_list(current['facts'])}</section>
        <section><h3>仍然存在的 Gap</h3>{render_list(current['open_gaps'])}</section>
        <section><h3>下一步</h3>{render_list(current['next_steps'])}</section>
      </div>
    </div>
  </section>
  <section class="wrap sources">
    <p class="eyebrow">SOURCE INDEX</p><h2 class="section-label">报告依据</h2>{source_html}
  </section>
  <footer>{esc(generated_note)} · 由 visualize-agent-work-summary 确定性生成</footer>
  <script>
    document.querySelectorAll('[data-filter]').forEach((button) => {{
      button.addEventListener('click', () => {{
        const selected = button.dataset.filter;
        document.querySelectorAll('[data-filter]').forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
        document.querySelectorAll('.phase').forEach((phase) => {{
          phase.hidden = selected !== 'all' && phase.dataset.status !== selected;
        }});
      }});
    }});
  </script>
</body>
</html>
"""


def check_html(text: str, phase_count: int) -> dict[str, Any]:
    checks = {
        "doctype": text.startswith("<!doctype html>"),
        "standalone_no_remote_assets": all(
            token not in text.lower()
            for token in ("<script src=", "<link rel=\"stylesheet\"", "@import url(")
        ),
        "phase_count": text.count('<article class="phase ') == phase_count,
        "status_filter": "data-filter=\"in_progress\"" in text,
        "evidence_index": "SOURCE INDEX" in text,
        "no_unsafe_url": "javascript:" not in text.lower() and "data:text/html" not in text.lower(),
    }
    return {"ok": all(checks.values()), "checks": checks, "phase_count": phase_count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Schema-version-1 report JSON")
    parser.add_argument("--output", required=True, type=Path, help="Standalone HTML destination")
    parser.add_argument("--check", action="store_true", help="Validate generated HTML and print a JSON check report")
    args = parser.parse_args()

    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        payload = validate_payload(raw)
        output = render(payload, args.input.name)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        result = check_html(output, len(payload["phases"]))
        if args.check:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif not result["ok"]:
            print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return 0 if result["ok"] else 1
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
