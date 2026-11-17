#!/usr/bin/env python3
"""Put the Vector CSS into an HTML page, or refresh it if it's already there.

Usage: python3 apply.py <page.html> [--tokens-only]

- Inlines dist/vector.css (or dist/tokens.css with --tokens-only) between
  /* @vector:start */ and /* @vector:end */ markers in a <style> block.
  If the markers exist, only the text between them is replaced, so the page's
  own CSS is never touched. Otherwise a new <style> block goes at the end of <head>,
  so the page's own styles can still override it.
- Adds the Google Fonts <link> tags for Inter and JetBrains Mono if they're missing.

Running it again is safe: it updates the page to the current dist/ build.
Inlining (not linking) keeps the page self-contained, which claude.ai
artifacts require.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))
from build import FONTS  # noqa: E402  (same folder; keeps the font tags in one place)

START, END = "/* @vector:start */", "/* @vector:end */"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    page_p = pathlib.Path(args[0]).expanduser()
    src = ROOT / "dist" / ("tokens.css" if "--tokens-only" in sys.argv else "vector.css")
    if not src.exists():
        sys.exit(f"{src} is missing: run python3 {ROOT / 'scripts' / 'build.py'} first")
    css = src.read_text().rstrip("\n")
    page = page_p.read_text()
    block = f"{START}\n{css}\n{END}"
    actions = []

    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if pat.search(page):
        page = pat.sub(lambda m: block, page, count=1)
        actions.append(f"refreshed the Vector block from dist/{src.name}")
    else:
        tag = f"<style>\n{block}\n</style>\n"
        m = re.search(r"</head\s*>", page, re.I)
        if m:
            page = page[:m.start()] + tag + page[m.start():]
        else:
            m = re.search(r"<body[^>]*>", page, re.I)
            at = m.start() if m else 0
            page = page[:at] + tag + page[at:]
        actions.append(f"added dist/{src.name} in a new <style> block")

    if "fonts.googleapis.com/css2?family=Inter" not in page:
        m = re.search(r"<head(?:\s[^>]*)?>", page, re.I)
        at = m.end() if m else 0
        page = page[:at] + "\n" + FONTS + "\n" + page[at:]
        actions.append("added the Inter and JetBrains Mono font links")

    page_p.write_text(page)
    print(f"{page_p}: " + "; ".join(actions) + ".")
    if not re.search(r"""class\s*=\s*["'](?:[^"']*\s)?vx(?:\s|["'])""", page):
        print('Add class="vx" to <body> (or a wrapper) for the base font and text colour.')


if __name__ == "__main__":
    main()
