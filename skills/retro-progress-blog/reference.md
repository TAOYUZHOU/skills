# Retro-progress embed map

## Public SSOT

| Page | Anchor | Owner of |
|---|---|---|
| `history/changelog.html` | `#current` | Live coverage / quality / wall / next |
| `history/changelog.html` | `#superseded` | Retired stars (M001 0.357, STREAM 0.17, +1.32 as this campaign, …) |
| `history/glossary.html` | term `id` | Dual, fill, score0, \(J\), hfstream, … |

Paper hero, 摘要, **§5 主表**, §8, and satellite heroes quote `#current`.
History banners cite the changelog, not paper §7.
Skill live-conclusions must match `#current`. If they disagree, the page wins.

## Where history cards sit

| Paper anchor | History page | Why there |
|---|---|---|
| nav / first viewport | `changelog.html`, `glossary.html` | Reader SSOT |
| `#method` §3 | `pns-lineage.html`, `from-score0.html` | Dual queues stay short |
| `#theory` §4 | `propositions.html` | Cartesian / exist / VIP / stop |
| `#app-a` | `bayes-pdvn.html`, `from-score0.html` | Bayes vs RL vs PDVN |
| `#systems` §7 | `roadmap.html` | Engineering timeline (not the current table) |
| `#systems` §7.1 | `m001-writeback.html`, `flux-017.html`, `atoms.html` | Dated proofs |
| `#systems` §7 | `cpu-bound.html` | Wall clock was CPU |
| `#prelim` §2.1 | paper `#score-formula` | How \(E\) / logS are computed |
| `#model` §7.2 / `#app-b` | `unary-complete.html`, `rho.html` | Measured Gantts, κ / ρ. Pedagogical OT Gantt is inline in appendix B |
| `#conc` §8 | `roadmap.html`, `early-stop-gp.html` | Dated next vs current next |
| `#exp` §5.2 / `#conc` §8 | `early-stop-gp.html` | 204-cell replay; not quality \(P_k\) |

## `/and-serial/` hash map

Keep in sync with `artifacts/and_serial_blog/index.html`:

```
changelog, log, ssot → changelog.html
glossary, 词表       → glossary.html
roadmap              → roadmap.html
early-stop, gp-stop  → early-stop-gp.html
panel, hfstream-full → /dual-hfstream-full/
default              → /retro-progress/
```

(Other hashes unchanged: pns, propositions, unary-complete, …)

## Publish checklist

- [ ] `changelog.html#current` is the only starred status block
- [ ] Hero / 摘要 / §5 主表 / §8 quote that block (same run, same deltas)
- [ ] §5 does not lead with retired +1.32
- [ ] History banners cite changelog, not §7 four-mol \(J\approx 1.7\)
- [ ] §7 four-mol table header is 通量标定, not 现状
- [ ] No「数字以论文为准」left in history index / builder
- [ ] Skill Live conclusions match `#current`
- [ ] New jargon has a glossary `id` **and** a `TERMS` row in `assets/glossary-link.js`
- [ ] Hero defines the idea in Chinese before the name; dotted links work (`.gloss-tip` from `data-tip`, not `title=`)
- [ ] Displaced number is in `#superseded` or a dated timeline item — not still in the hero
- [ ] No “不要星 X” as the main sentence; write the current number
- [ ] Satellite report hero agrees or explicitly says “this page is the dated report for DATE”
- [ ] `history/index.html` lists new pages
- [ ] Hash redirect updated
- [ ] CSS/JS `?v=` bumped
- [ ] curl paper / changelog / glossary → 200

## Rebuild

`build_history.py` rebuilds dated pages from the and-serial archive. **Do not run it** to refresh changelog, glossary, or the paper. Those are hand-edited SSOT.

Do not paste the full 3500-line and-serial note back into the paper.
