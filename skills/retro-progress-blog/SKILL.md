---
name: retro-progress-blog
description: >-
  Write and update the Retro Engine reader site at /retro-progress/:
  that site is the public SSOT. Changelog owns current numbers, glossary
  owns jargon (dotted links + large hover tip). Use when editing
  retro-progress, and-serial, 技术报告, 技术blog, 论文式博客, changelog,
  变更日志, 词表, glossary, history, writing norms, or paper conclusions.
---

# Retro Progress Blog

The **public site is the SSOT**. Chat, this skill, `c12_search/CHANGELOG.md`, and satellite reports must not invent a newer “现状”. If they disagree with the site, **the site wins** — fix this skill in the same edit.

Canonical: `http://161.189.194.243/retro-progress/`
Source: `retro-engine/artifacts/retro_progress_blog/`

Publish + visual bar: `public-html-report`. No trycloudflare. Do not kill `/production/r3s`.

## Who owns what

| Fact | File | Rule |
|---|---|---|
| Current numbers / next action | `history/changelog.html` `#current` | Only starred status block. Hero, 摘要, §5 主表, §8 quote it. |
| Retired stars | `history/changelog.html` `#superseded` | Dated history only. Never first table in §5, never hero, never 「现状」 header. |
| Jargon | `history/glossary.html` + `assets/glossary-link.js` | New name = glossary `id` + `TERMS` row + first-use human sentence. |
| Argument | `index.html`, `history/*.html` | Paper = now (quotes `#current`). History = dated proof. |

Do **not** write「数字以论文为准」or「以论文 §7 四分子表为准」。History banners cite the changelog. §7 is four-mol **flux calibration**, not the 225-cell panel. The four-mol table header must say 通量标定, not 现状.

Do **not** run `build_history.py` to refresh SSOT pages. That script overwrites dated history from the and-serial archive. Changelog, glossary, and the paper are hand-edited.

## Live conclusions (do not write the opposite)

Copy these; do not restore an older win as present tense.

- **Coverage:** Dual ≈ production cartesian (BH 110/119 vs 107; patent 94/106 vs 95).
- **Wall:** Dual is **slower** on the panel (BH 1.38×, patent 1.59×). Do not write that Dual beat production wall clock.
- **Quality (this campaign):** clean ΔlogS is identity-aligned \((mapped\ rxn, known)\). BH rerank median **+0.10** (mean +0.61, 87, 46 wins). Patent clean **77**, median **+1.08** (mean +2.75, 61 wins). Quote median as typical. OR-cache patent **+0.43** and old 86-overlap **+1.32** are retired.
- **Flux:** panel median \(J\approx 0.91/1.02\). Four-mol \(J\approx 1.7\) is a dedicated calibration, not the 225-cell rate.
- **Bound:** remote 5015 POST. Not `expand_one` copy.
- **Early stop:** decide at **iteration** boundary. 204-cell first_solve saves **51% wall** on solved-count, not quality. \(P_k(H)=\Pr(\)next \(H\) iters beat top-1\()\) needs new \(s_k\). Do not write “50% wall, quality holds”.
- **Next:** early stop before another fill/\(B\) sweep or a second scoring GPU. No more pipeline-overlap cuts.

## Conflict scan (after every number landing)

Grep the paper + history banners + satellite heroes. Present tense must not still say:

| Trap | Write instead |
|---|---|
| Dual 墙钟赢了生产笛卡尔积 | Dual 中位更慢 1.4–1.6× |
| 这次面板质量 +1.32 或专利 OR 缓存 +0.43 | BH +0.10 / 专利 +1.08；旧数进 `#superseded` |
| 四分子 \(J\approx 1.7\) 是面板速率 / 「现状 · hfstream Dual」 | 通量标定；面板 \(J\approx 0.91/1.02\) |
| first_solve 51% 且质量不掉 | 条数停；\(P_k\) 还缺 \(s_k\) |
| M001 \(J=0.357\) / STREAM 0.17 是当前通量 | `#superseded` |
| bound = expand 拷贝 | 远端 5015 POST |
| 数字以论文 / §7 为准 | 数字以变更日志 `#current` 为准 |

## Land a number

1. Edit `#current` (and `#superseded` / timeline) first.
2. Quote it in hero, 摘要, **§5 主表**, §8.
3. Demote the old star. Never two current tables. Never leave §7 labeled 现状.
4. Update **this skill’s Live conclusions** in the same edit.
5. Satellite (`/dual-hfstream-full/`) cites `#current` or dates itself.
6. Run the conflict scan. Bump `?v=`. Verify paper / changelog / glossary 200.

## Land a term

Same edit, all three:

1. `glossary.html` stable `id` ([templates/glossary-term.html](templates/glossary-term.html)).
2. `assets/glossary-link.js` `TERMS`: longest phrase first, `id`, one-line `title` (the hover text).
3. First viewport: Chinese clause, then the name in parentheses.

Linker: every reader HTML includes `glossary-link.js`. Dotted underline → `#id`. Hover = large `.gloss-tip` from `data-tip` (**not** `title=`). Shop-talk that colleagues ask about (瓦 / 每瓦 / 整瓦 / tile, bound, INIT, 量子, 前沿, 物化, 挂边, pn) must be registered.

**Symbols:** first \(J,T,D,E,\mathrm{logS},s_{\mathrm{cand}},r,R^2\) in the paper get a Chinese gloss **in that sentence**. Appendix may derive; it may not introduce.

How \(E\) / \(\mathrm{logS}\) are computed lives in paper **§2.1** (`#score-formula`) and glossary `#E` / `#logs` / `#known` / `#str`. Do not leave the main text as 「各步分数的乘积再取对数」without the known / STR cases. Do not write “unknown + STR beats known on the same \(A\)” as the design — that C105 inversion is a rescore identity mismatch (mapped-\(A\) cached as known, dump flag flipped by `rxn0`). Optimal-transport appendix B must keep the inline 3-lane Gantt (serial vs stream); do not point only at `history/unary-complete.html`.

## Layers

| Layer | Voice | Allowed |
|---|---|---|
| `#current` | Present. One block. | Coverage, quality, wall, flux, next. |
| Paper | Present. | Quote `#current`. §5 主表 = panel. §7 = four-mol flux only. |
| History | Dated. | Proofs. Banner → changelog, not §7. |
| Glossary | Timeless. | What / not what. No campaign scores. |

No “不要星 X” as the main sentence — put X in `#superseded` and write the live number.

## Writing voice

- Short sentences. Run directory + date.
- 已落地 / 未测 / 计划中 in the same paragraph if a knob could be confused.
- First viewport defines the idea, then names it.
- Assumptions table for model numbers.
- Chinese body, KaTeX, paper/teal. No dashboard chrome.

## Model / hardware (unchanged)

- `tile_s` are not physical constants.
- Predict \(J=n/T_{\mathrm{round}}\). Whole-tree \(T\) error is expected.
- No theoretical / capacity Pareto while bound is remote 5015.
- No unlanded B/fill stars. Do not rerun cartesian M089. Do not rematrix Dual 119+106 unless asked.

## History proof pages

[templates/history-subpage.html](templates/history-subpage.html) + [templates/hist-card.html](templates/hist-card.html). Banner must cite changelog. Register in `history/index.html` and `and_serial_blog` hash map. Do not run `build_history.py` to refresh SSOT. Restart `scripts/restart_retro_progress_blog.sh` only if the static server died.

Dated voice: landed work is past tense. Do not leave 「下一步才是批 BBL / 改 expand 拷贝」or 「墙钟待新 once_ov」after those runs finished. Then-plans stay as 「当时写下的下一刀」. Current next lives only in `#current` (early stop). First viewport on history index defines AND-serial in Chinese before the old `/and-serial/` bookmark.

## Templates / more

- [templates/changelog-entry.html](templates/changelog-entry.html)
- [templates/glossary-term.html](templates/glossary-term.html)
- [templates/paper-spine.html](templates/paper-spine.html)
- [reference.md](reference.md)
