# HTML visual bar — starter patterns

## CSS variables (pick one coherent palette)

```css
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Source+Sans+3:wght@400;600&display=swap');

:root {
  --bg0: #0f1419;
  --bg1: #1a2332;
  --ink: #e8eef6;
  --muted: #9aa8b8;
  --accent: #3d9a7a;
  --warn: #c4a35a;
  --danger: #c45c5c;
  --font-display: "Fraunces", Georgia, serif;
  --font-body: "Source Sans 3", system-ui, sans-serif;
}

body {
  margin: 0;
  font-family: var(--font-body);
  color: var(--ink);
  background:
    radial-gradient(1200px 600px at 10% -10%, #243044 0%, transparent 55%),
    linear-gradient(165deg, var(--bg0), var(--bg1));
  min-height: 100vh;
}

h1, h2 { font-family: var(--font-display); font-weight: 600; letter-spacing: -0.02em; }
```

Light alternative: warm off-white field + ink charcoal + single accent (avoid purple-gradient cliché).

## Page skeleton

```html
<header class="hero">
  <p class="brand">Team / Project</p>
  <h1>Report title</h1>
  <p class="lede">One sentence: what was compared and what to look at.</p>
</header>
<nav><!-- overview | detail --></nav>
<main>
  <section><!-- primary finding --></section>
  <section><!-- tables / charts --></section>
</main>
```

## Empty state

```html
<div class="empty">
  <h2>No route found</h2>
  <p>Search finished under mssr=8 with open paths remaining. Not a transport failure.</p>
</div>
```

Do not show raw `/home/ubuntu/...` paths in the empty state.
