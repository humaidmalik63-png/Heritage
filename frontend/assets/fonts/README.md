# Fonts

This folder is intentionally empty.

The application loads **no font files at runtime** and fetches nothing from a
CDN. Typography is resolved from a system font stack declared in `styles.css`:

```css
--font-sans:  "Inter", "Inter var", "Segoe UI Variable Text", "Segoe UI", system-ui, …
--font-label: "Chakra Petch", "Bahnschrift", "DIN Condensed", "Agency FB", "Arial Narrow", …
```

* Body copy uses `Inter` when installed, otherwise the operating system's UI
  sans-serif.
* Labels and micro-type use a geometric condensed face; on Windows this
  resolves to **Bahnschrift**, which ships with the OS.

## Why nothing is bundled

The project has no self-hosted font files: the only `.woff2` assets under
`frontend/` are hashed build artefacts inside `frontend/.next/static/media/`,
which are not a redistributable source of fonts. Downloading Inter or Chakra
Petch from Google Fonts at runtime is not permitted by the frontend spec.

## Adding real self-hosted fonts

If you obtain licensed `.woff2` files (Inter and Chakra Petch are both OFL),
drop them in this folder and declare them in `styles.css`:

```css
@font-face {
  font-family: "Inter";
  src: url("assets/fonts/inter-latin.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap;
}
```

No other change is required — the stacks above will pick them up.