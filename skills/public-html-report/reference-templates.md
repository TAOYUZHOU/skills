# Template workflow (condensed)

Executable summary of the external library
`beautiful-html-templates`. **Authoritative detail** remains that repo's
`AGENTS.md` — if this file and `AGENTS.md` disagree, follow `AGENTS.md`.

## Locate the library

```bash
TEMPLATES="${BEAUTIFUL_HTML_TEMPLATES:-/root/autodl-tmp/taoyuzhou/beautiful-html-templates}"
# if missing:
# git clone https://github.com/zarazhangrui/beautiful-html-templates "$TEMPLATES"
```

Key files:

| Path | Role |
|------|------|
| `$TEMPLATES/index.json` | Catalog: mood, tone, best_for, formality, density, scheme |
| `$TEMPLATES/templates/<slug>/` | Full template (HTML + CSS + nav runtime + assets) |
| `$TEMPLATES/AGENTS.md` | Full operating manual |

## Workflow (do not skip)

### 1. Ask occasion + mood

Before reading `index.json`, ask and **wait**:

> 1. What's the occasion?
> 2. What mood / vibe?

Ask about *tone*, not industry. Good: “polished & authoritative vs warm & design-led?” Bad: “finance or tech?”

### 2. Pick 3 candidates from `index.json`

Match user answers to `mood`, `tone`, `best_for`, `formality`. Sanity-check `density` and `scheme`. Treat `occasion` as soft signal; `avoid_for` as soft warning (user taste wins if they insist).

Pick three that are **different enough** — e.g. one editorial, one warmer, one wildcard — not three near-clones.

| Field | Use |
|-------|-----|
| `mood` | Feeling keywords |
| `tone` | Voice / personality |
| `best_for` | Lead when narrating the pick |
| `avoid_for` | Soft clash warning |
| `formality` | Audience sanity check |
| `density` | Content volume fit |
| `scheme` | Hard filter if user wants light/dark |
| `slide_count` | How many demo layouts exist |

Only deep-read a template's HTML/CSS after shortlisting.

### 3. Title-slide previews

For each of the 3:

1. Read that template's `template.html` (or equivalent entry HTML).
2. Keep **only the cover / title slide**.
3. Replace placeholders with the user's **real** title, subtitle, author, date.
4. Save under e.g. `previews/01-<slug>.html` with all sibling assets (`styles.css`, `deck-stage.js`, fonts, images) so the preview opens correctly.

### 4. Present paths; wait for pick

Send absolute paths (one per line). On macOS: `open <path>`. On Linux/AutoDL: use browser tools if available; otherwise paths alone.

Wait for the user to choose. Do not prose-debate aesthetics instead of showing previews.

### 5. Build the full deck

1. Clone the chosen template **folder** into the project workspace.
2. Adapt every slide (preserve / replace below).
3. Need more slides → duplicate an existing layout; fewer → drop from the bottom. Update page numbers (`NN / TT`).
4. Missing layout → design it **inside** that template's design system only (same fonts, palette, decoration, spacing, chrome, nav). Do not switch templates mid-deck. Do not mash two templates.

### 6. Output contract

After every artifact (previews, iterations, final):

1. Open in browser when possible.
2. Send the **absolute file path** on its own line.

For the final deck: one-line tone rationale + caveats (e.g. which slides were designed from scratch).

## Preserve vs replace

**Always preserve (the design system)**

- Fonts and Google Font imports — never substitute (no “Inter is close enough”)
- `:root` colors / palette — never recolor
- Layout grid, slide-level CSS classes
- Decorative elements (brackets, grain, doodles, SVGs)
- Navigation runtime (`deck-stage.js`, keyboard handler, scroll-snap, etc.)

**Always replace (user content)**

- Headlines, body copy, lists, captions
- Stats / numbers, names, dates, attributions
- Section labels / chrome tokens (`[Topic]`, `[Year]`, …)
- Image placeholders — same dimensions as the template expects

## Extending a template (missing layouts)

Same fonts, weights, letter-spacing; same CSS variables (closest accent if needed); same decorative vocabulary; same padding/grid rhythm; same component grammar (e.g. stat card structure); same chrome; same nav integration.

Test: place the new slide between two original slides — it must look native, not grafted.

## Tone-first matching

Templates have **tones**, not industries. A confident editorial deck can carry a tech talk if the user wants design-led. Lead with `mood` + `tone` + `best_for`. Flag formality mismatches (e.g. low-formality for a board deck) even when tone overlaps.

## Common pitfalls

- Skipping Step 1 or Step 4 (previews)
- Substituting fonts or recoloring accents
- Combining layouts from different templates
- Stripping “extra” decoration
- “Modernizing” a template instead of picking another
- Narrating a long transcript instead of path + one-line rationale
