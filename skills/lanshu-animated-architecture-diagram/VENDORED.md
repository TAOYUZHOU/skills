# Lanshu Animated Architecture Diagram (vendored)

Upstream: [cclank/lanshu-animated-architecture-diagram](https://github.com/cclank/lanshu-animated-architecture-diagram) (MIT)

Vendored into `TAOYUZHOU/skills` for Codex/Cursor agent use.

## Local patches (this fork)

- **Linux font paths** — DejaVu/Liberation fallbacks in `scripts/render_animated_diagram.py`
- **Pillow &lt; 9.1** — `Image.Resampling` compatibility shim

## Quick use

```bash
python skills/lanshu-animated-architecture-diagram/scripts/render_animated_diagram.py \
  --spec path/to/spec.json \
  --outdir path/to/output \
  --basename my-diagram \
  --verify --check
```

See [SKILL.md](./SKILL.md) and [references/spec-format.md](./references/spec-format.md).

## Example in retro-engine

- Spec: `retro-engine/docs/diagrams/hypergraph_single_step_spec.json`
- Outputs: `hypergraph_single_step.{png,gif,excalidraw}`
