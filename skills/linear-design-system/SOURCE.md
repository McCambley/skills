# Where Vector came from

Vector started as a Design System artifact on claude.ai, made with Claude's design tools. This skill is a standalone copy of it, so it works offline and doesn't depend on access to the original artifact. If you keep a link to your own original, put it in `SOURCE.local.md` next to this file. Files named `*.local.*` stay on your machine and are never published.

## Changes from the original artifact

- The component previews were replaced by one generated gallery (`dist/gallery.html`), because the originals loaded icons from `/_blob/` addresses that only work inside the artifact.
- Generated CSS was added: `vx-t-<style>` type classes, `vx-ico` icon classes, `body.vx` page background, and no font ligatures in mono text. Without the last change, `--` displays as a dash in class names.
- The Google Fonts `@import` moved out of the CSS and into `<link>` tags, so the CSS can sit anywhere in a page.
- The tokens are unchanged.

## Skills that use this one

The `build-board` skill reads `tokens.json` and `icons/` from this folder to generate its page template (`build-board/scripts/sync_design_system.py`). After you change Vector here, run that script so boards match.

## Re-syncing from an original artifact

If you have the original Design System artifact (see `SOURCE.local.md`):

1. Read the system with the Artifact tool, using its bare URL:
   - `read` with `path` for `project/tokens.json`, `project/README.md` and `project/components/bundle.css`.
   - For icons, `list` with `scope: "assets"`, then `read` each asset id one at a time with `path`. A multi-path read doesn't fetch assets.
   - The index file `project/design-system.json` maps asset ids to icon names under `assetGroups.Icons.files`.
2. Replace the matching files here:
   - `tokens.json`
   - `references/brand.md`, from `README.md`
   - `icons/<name>.svg`
   - `src/components.css`, from `bundle.css`. Keep the additions listed above, and drop the `@import` line.
3. Run `python3 scripts/build.py`, then screenshot the gallery in both themes with `scripts/check.py dist/gallery.html --screenshot …`.
4. Run `python3 ~/.claude/skills/build-board/scripts/sync_design_system.py` so boards pick up the change.
