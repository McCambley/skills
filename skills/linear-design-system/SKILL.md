---
name: linear-design-system
description: Style pages, artifacts, apps and other UI with Vector, the user's own design system in the style of linear.app. It has near-black canvases, hairline gradient borders lit from the top, colour only in icons and one indigo accent, Inter and JetBrains Mono type, and light and dark themes. Provides ready-made CSS (tokens, type classes, cards, buttons, badges, icon tiles, glow sections, ten icons), scripts that inline it into an HTML page and check a page against the brand rules, and a gallery. Use whenever the user asks for their design system, Vector, "the Linear look" or "Linear style", or a dark, quiet, Linear-like UI, for HTML pages, claude.ai artifacts, React or other web apps, dashboards, slides or charts.
---

# Vector design system

Vector is a quiet, precise interface system styled after the look of linear.app. It is original: its name, icons and tokens are its own. This skill is self-contained and doesn't depend on any other skill. The `build-board` skill builds its page styles from it.

**Never put Linear's name, logo or artwork on what you make.** The system is called Vector. Page titles and copy describe the user's product, not Linear.

## What's here

All paths are relative to this skill's folder, `~/.claude/skills/linear-design-system/`.

| Path | What it is |
|---|---|
| `references/brand.md` | The brand book. **Read it before designing anything with Vector.** |
| `references/components.md` | Usage rules for each component. |
| `dist/vector.css` | Everything in one file: tokens, type classes, components and icons. Generated, so don't edit it. |
| `dist/tokens.css` | Only the CSS variables, for projects with their own components. |
| `dist/gallery.html` | A page showing every token, type style, component and icon in both themes. Open it in a browser. |
| `tokens.json` | The source of truth for colours, type, spacing, radii and shadows. |
| `icons/*.svg` | Ten two-tone icons, for use as files or `<img>`. |
| `src/components.css`, `src/gallery.html` | The sources `scripts/build.py` builds from. |
| `scripts/apply.py` | Inlines the CSS into an HTML page, or refreshes it. |
| `scripts/check.py` | Checks a page against the rules, and screenshots it in both themes. |
| `scripts/build.py` | Rebuilds `dist/` after you change a source. It also checks contrast. |

The scripts need only Python 3. Screenshots need Google Chrome or Chromium.

## Use it in a single HTML page or a claude.ai artifact

1. Read `references/brand.md`. Skim `dist/gallery.html` if you need to see a component.
2. Write the page's markup with the Vector classes (listed below). Give `<body>` the class `vx`. Write the page's own CSS with tokens only: `var(--bg-raised)`, `var(--space-4)`, `var(--t-body-size)` and so on. Never add raw colours. If you need a new semantic colour, define a variable from a token, for example `--status-done: var(--icon-green);`.
3. Inline the system:
   ```sh
   python3 ~/.claude/skills/linear-design-system/scripts/apply.py <page.html>
   ```
   This puts `dist/vector.css` between `/* @vector:start */` and `/* @vector:end */` markers at the end of `<head>`, so the page's own styles can override it. It also adds the Google Fonts links. Running it again refreshes the block and leaves the rest of the page alone.
4. Check the page and look at both screenshots:
   ```sh
   python3 ~/.claude/skills/linear-design-system/scripts/check.py <page.html> --screenshot <scratch>/page
   python3 ~/.claude/skills/linear-design-system/scripts/check.py <page.html> --screenshot <scratch>/page-phone --width 390
   ```
   Fix every ERROR. A WARN is a brand rule: fix it unless the page has a real reason not to follow it.

   **No one-sided borders on rounded elements.** A rounded element has a border on all four sides or none, never a stripe such as `border-left` (it looks like a fingernail). See "No one-sided borders on rounded elements" in `references/brand.md`. The checker reports it as an ERROR.

For a claude.ai artifact, still follow the Artifact tool's contract, including its design skill. Vector supplies the visual system, and it already meets the contract's styling rules:
- Colours are tokens on `:root`.
- Dark mode sits under `prefers-color-scheme`, guarded by `:root:not([data-theme="light"])`, and also under `:root[data-theme="dark"]`.
- `body.vx` sets the page background.
- Fonts come only from Google Fonts, which the contract allows, and everything else is inline.

Don't link to files in `~/.claude`, because a published page can't reach them.

## Use it in a project with a build step (React, Vite, Next.js and others)

1. Copy `dist/vector.css` (or `dist/tokens.css`) into the project, for example `src/styles/vector.css`, and import it once at the app root. Copy the file rather than pointing at `~/.claude`, so the project still builds on other machines.
2. Add the font tags below to the HTML `<head>`, or self-host Inter and JetBrains Mono.
3. Copy any icons you need from `icons/` into the project's assets, or use the `vx-ico` classes, which carry the icons inside the CSS.
4. To update the project later, copy the file again. The header comment gives the version.
5. Check the project's own stylesheets with `python3 ~/.claude/skills/linear-design-system/scripts/check.py <file.css>`. For a `.css` file it runs only the CSS checks: unknown tokens, raw colours and one-sided borders on rounded elements.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;550;600&family=JetBrains+Mono:wght@400&display=swap">
```

With Tailwind, map theme colours to the variables (`colors: { base: 'var(--bg-base)', ... }`) rather than copying hex values, so both themes keep working.

## Use it outside HTML (slides, documents, charts, images)

Take values from `tokens.json`. Each colour token has `dark` and `light` values and a `usage` note. Pick one theme and keep to it. Dark is the primary theme. The same rules apply: use neutral surfaces, keep colour for icons, data marks and one accent, use Inter for text and JetBrains Mono for keys and code, and write in sentence case. For a chart, use the `icon-*` hues as series colours and keep each hue tied to one meaning.

## Class reference

| Class | Use |
|---|---|
| `vx` | On `<body>` or a wrapper: Inter, `text-primary`. On `<body>` it also sets the page background. |
| `vx-card`, `vx-card--accent` | Every card and panel. Use the accent version on one featured card per page. |
| `vx-glow` | A hero or feature section background. Use one per screen. |
| `vx-btn` plus `--primary`, `--secondary` or `--ghost`, and `--lg` if needed | Buttons. Use one primary button per view. |
| `vx-kbd` | A keyboard shortcut inside a button or text: `⌘K`. |
| `vx-badge` plus `--blue`, `--amber`, `--violet`, `--green` or `--red`, with an `<i></i>` dot | Status chips. Colour goes only in the dot. |
| `vx-icontile vx-icontile--<hue>` | A 36px tile holding one icon, in feature cards and empty states. |
| `vx-ico vx-ico--<name>`, plus `vx-ico--lg` for 20px | An icon as a CSS class. Add `aria-hidden="true"` when it's decorative. Names: inbox, issues, cycles, projects, roadmap, insights, triage, integrations, teams, docs. |
| `vx-t-<style>` | Type styles: display, title-1, title-2, body-lg, body, label, micro, mono. |

Variables follow the token names. Colour variables include `--bg-base`, `--text-secondary`, `--accent`, `--icon-green` and `--soft-green`. Spacing and shape use `--space-4`, `--radius-lg` and `--shadow-card`. Type uses `--font-sans`, `--font-mono` and `--t-<style>-size`, `-lh`, `-weight` and `-track`.

## The rules that matter most

The full rules are in `references/brand.md`. In short:

- Surfaces, text and borders are grey. Colour appears only in icons, status dots, one `accent` action per view, and faint glows.
- Each object type keeps one icon hue everywhere.
- Cards use the gradient border from `vx-card`, never a flat grey outline. Shadows are only for things that float, such as menus and popovers.
- Glows stay faint, with at most two per section and one glow section per screen.
- Text keeps 4.5:1 contrast in both themes. The text tokens already meet it, so don't invent lighter greys.
- Copy is sentence case, buttons are verbs, and there are no exclamation marks or emoji. Keys and shortcuts are set in mono.
- Check both themes before you call anything done.

## Changing the system

1. Edit the source: `tokens.json`, `src/components.css`, `icons/*.svg` or `src/gallery.html`. Never edit `dist/`.
2. Rebuild:
   ```sh
   python3 ~/.claude/skills/linear-design-system/scripts/build.py
   ```
   It refuses to write if the CSS uses an undefined token or a text, link, accent or icon colour fails contrast. Run it with `--check` to confirm `dist/` is current without writing anything.
3. Screenshot the gallery in both themes with `scripts/check.py dist/gallery.html --screenshot …` and look at the images.
4. Pages that inlined the old CSS keep it until you run `apply.py` on them again. Projects that copied `dist/vector.css` keep the old version until the file is copied again.

New icons follow `icons/README.md`: a 24px grid, 1.5px rounded strokes, one hue, and a 22% fill on part of the shape. Give an icon a new hue only when it names a new object type.

**Known issue:** in the dark theme, white text on a hovered primary button (`accent-hover`) is 3.84:1, below 4.5:1. `build.py` reports it as a warning. Fixing it means darkening `accent-hover.dark`, and that's the user's design decision, so ask before changing it.

`SOURCE.md` records where Vector came from, which skills use it, and how to re-sync it from an original Vector artifact.
