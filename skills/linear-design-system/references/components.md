# Vector components

Every class below is defined in `dist/vector.css`. Read `brand.md` for the rules behind them.

## Card

A surface with a thin gradient border that is lit from the top, and a faint inner tint. Use it for every card and panel.

**Usage**
- `class="vx-card"` on any block. It pads `space-6`, rounds to `radius-lg` and sits on `bg-raised`.
- Add `vx-card--accent` to one featured card per page for the indigo-to-orange border (`edge-accent-a` → `edge-accent-b`).
- Never add a one-sided border (`border-left`, `border-top` and so on) to a card or any other rounded component. It looks like a fingernail. Use an icon, a badge or `vx-card--accent` instead.
- Put a `vx-icontile` first, then an `h3` title and a `p` description. The consumer provides the content and the grid (gap `space-4`).
- Hover brightens the middle of the border to `border-strong`. Do not add `shadow-card` to cards in a grid.


## Button

Three button styles: a lit indigo primary, a secondary with a gradient border, and a quiet ghost.

**Usage**
- `vx-btn vx-btn--primary`: the one main action per view. `accent` fill, a soft top highlight, `shadow-button`, `on-accent` text.
- `vx-btn vx-btn--secondary`: every other bordered action. `bg-elevated` fill with an `edge-highlight` → `border-subtle` border.
- `vx-btn vx-btn--ghost`: toolbar and nav actions. `text-secondary`, washes to `bg-hover` on hover.
- Add `vx-btn--lg` (40px) for hero calls to action; the default is 32px. A 16px icon may lead the label; a `vx-kbd` shortcut may follow it.
- Labels are verbs in sentence case. Focus shows a 2px `accent` outline.


## Badge

A pill for status and labels: a coloured dot and a short label inside a hairline gradient border.

**Usage**
- `vx-badge` with a leading `<i>` dot. Tone classes set the dot: `vx-badge--amber` (in progress), `--green` (done), `--violet` (in review), `--red` (urgent), `--blue` (todo); none is grey (backlog).
- The label is `text-secondary`; colour lives only in the dot, so the word carries the meaning.


## IconTile

A 36px rounded tile that holds one colourful icon on its matching soft tint, inside a gradient border.

**Usage**
- `vx-icontile vx-icontile--<hue>` around one 20px icon from the Icons group. Match the hue to the icon: `--blue` for Inbox, `--violet` Issues, `--amber` Cycles, `--green` Projects, `--teal` Roadmap, `--pink` Insights, `--orange` Triage, `--red` Integrations, `--indigo` Teams; no hue class for Docs.
- Use it in feature cards and empty states. In lists and nav, show the bare icon at 16px instead.


## GlowSection

A section background with a faint indigo glow from the top and a small warm glow to one side, for heroes and feature bands.

**Usage**
- `class="vx-glow"` on a full-width section. It paints `glow-accent` and `glow-warm` as radial gradients over `bg-base`.
- One glow section per screen. Text on it uses the normal text tokens; the glows stay faint enough that contrast holds.
- The consumer provides the content: usually a `display` headline, `body-lg` subcopy in `text-secondary`, and a primary plus secondary button.

