#!/usr/bin/env python3
"""Check an HTML page against the Vector rules, and optionally screenshot it.

Usage: python3 check.py <page.html | styles.css> [--screenshot <out_prefix>] [--width 1280]

A .css file (for example an app's own stylesheet) gets only the CSS checks.

ERROR (exit 1):
  - var(--x) used but defined neither by Vector nor by the page itself
  - a rounded element with a border on only some sides (a "fingernail"): a rule
    that sets border-radius and also a one-sided border such as border-left.
    Rounded elements have a border on all four sides or none. Only rules that
    set both in the same block are seen, so still check by eye.
WARN:
  - no Vector CSS in the page, or a Vector block older than the current dist/
  - the Inter / JetBrains Mono font links are missing
  - raw colours (hex, rgb, hsl) in the page's own CSS, outside the Vector block.
    The rule is tokens only. A page may define its own variables from tokens.
  - more than one primary button, accent card or glow section in the markup.
    The brand allows one of each per view; markup built by JavaScript isn't seen.

--screenshot renders the page in headless Chrome twice, writing
<out_prefix>-light.png and <out_prefix>-dark.png, so both themes can be checked.
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))
from build import defined_vars  # noqa: E402

START, END = "/* @vector:start */", "/* @vector:end */"
CHROME_PATHS = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"]
RAW_COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\([^)]*\)")
SIDE_BORDER = re.compile(r"(?<![\w-])border-(?:left|right|top|bottom|inline|block)(?:-start|-end)?(?:-width|-style)?\s*:\s*([^;}]*)", re.I)
RADIUS = re.compile(r"(?<![\w-])border(?:-[a-z]+)*-radius\s*:\s*([^;}]*)", re.I)
NO_BORDER = re.compile(r"^\s*(?:none|hidden|0(?:px|rem|em)?|initial|unset)\s*(?:!important)?\s*$", re.I)
ZERO_RADIUS = re.compile(r"^\s*(?:0(?:px|rem|em|%)?\s*)+(?:!important)?\s*$", re.I)


def fingernails(css):
    """Selectors whose rule sets a non-zero border-radius and a one-sided border."""
    found = []
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for sel, block in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if not any(not ZERO_RADIUS.match(v) for v in RADIUS.findall(block)):
            continue
        sides = [v for v in SIDE_BORDER.findall(block) if not NO_BORDER.match(v)]
        if sides:
            found.append(" ".join(sel.split()))
    return found


ALLOWED_RAW = re.compile(r"rgba?\(\s*(?:0\s*,\s*){3}0\s*\)|rgba?\(\s*255\s*,\s*255\s*,\s*255\s*,\s*0\s*\)")


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        sys.exit(__doc__)
    page_p = pathlib.Path(args[0]).expanduser()
    opt = lambda k: args[args.index(k) + 1] if k in args else None
    page = page_p.read_text()
    css_only = page_p.suffix.lower() == ".css"
    if css_only:
        page = "<style>/* stylesheet */\n" + page + "\n</style>"
    tokens = json.loads((ROOT / "tokens.json").read_text())
    errors, warns = [], []

    m = re.search(re.escape(START) + r"\n?(.*?)\n?" + re.escape(END), page, re.S)
    vector_block = m.group(1) if m else ""
    if css_only:
        pass
    elif not m:
        warns.append("no Vector block: run scripts/apply.py on this page "
                     "(a page that loads dist/vector.css as a file is fine; ignore this)")
    else:
        current = {(ROOT / "dist" / n).read_text().rstrip("\n") for n in ("vector.css", "tokens.css")}
        if vector_block.rstrip("\n") not in current:
            warns.append("the Vector block differs from the current dist/ build: run scripts/apply.py to refresh it")
    if not css_only and "fonts.googleapis.com/css2?family=Inter" not in page:
        warns.append("Inter / JetBrains Mono font links are missing: run scripts/apply.py, or add the tags from SKILL.md")

    # The page's own CSS: <style> contents minus the Vector block, plus style="" attributes.
    styles = re.findall(r"<style[^>]*>(.*?)</style>", page, re.S | re.I)
    own_css = "\n".join(styles)
    if m:
        own_css = own_css.replace(m.group(0), "")
    inline = re.findall(r"""style\s*=\s*("[^"]*"|'[^']*')""", page, re.I)
    own_all = own_css + "\n" + "\n".join(inline)

    page_vars = set(re.findall(r"(?<![\w-])--([a-zA-Z0-9_-]+)\s*:", own_all))
    js_vars = set(re.findall(r"""setProperty\(\s*['"]--([a-zA-Z0-9_-]+)""", page))
    used = set(re.findall(r"var\(--([a-zA-Z0-9_-]+)", own_all))
    known = defined_vars(tokens) | page_vars | js_vars | {"tile"}
    for v in sorted(used - known):
        errors.append(f"var(--{v}) is not a Vector token and the page doesn't define it")

    no_uris = re.sub(r"url\(\s*(['\"]?)data:.*?\1\s*\)", "", own_all, flags=re.S)
    raw = sorted({c for c in RAW_COLOUR.findall(no_uris) if not ALLOWED_RAW.fullmatch(c)})
    if raw:
        shown = ", ".join(raw[:8]) + (f" and {len(raw) - 8} more" if len(raw) > 8 else "")
        warns.append(f"raw colours in the page's own CSS ({shown}): use tokens instead")

    for sel in fingernails(own_css):
        errors.append(f"'{sel}' is rounded and has a one-sided border (a fingernail): border all four sides or none")
    for attr in inline:
        if fingernails("x{" + attr.strip("\"'") + "}"):
            errors.append(f"an inline style is rounded and has a one-sided border (a fingernail): {attr[:80]}")

    body = re.sub(r"<style.*?</style>|<script.*?</script>", "", page, flags=re.S | re.I)
    for cls, what in [("vx-btn--primary", "primary buttons"), ("vx-card--accent", "accent cards"), ("vx-glow", "glow sections")]:
        n = len(re.findall(r"""class\s*=\s*["'][^"']*\b%s\b""" % re.escape(cls), body))
        if n > 1:
            warns.append(f"{n} {what} in the markup; the brand allows one per view")

    for w in warns:
        print("WARN  " + w)
    for e in errors:
        print("ERROR " + e)
    print(f"\n{page_p.name}: {len(errors)} error(s), {len(warns)} warning(s).")

    shot = opt("--screenshot")
    if shot:
        chrome = next((c for c in CHROME_PATHS if pathlib.Path(c).exists()), None)
        if not chrome:
            print("No Chrome or Chromium found, so no screenshots. Open the page in a browser instead.")
        else:
            width = int(opt("--width") or 1280)
            for theme in ("light", "dark"):
                if re.search(r"<html\b", page, re.I):
                    themed = re.sub(r"<html\b[^>]*>", lambda t: re.sub(r"\s+data-theme=(\"[^\"]*\"|'[^']*'|\S+)", "", t.group(0))
                                    .replace("<html", f'<html data-theme="{theme}"', 1), page, count=1, flags=re.I)
                else:
                    themed = f'<html data-theme="{theme}">' + page
                out = pathlib.Path(f"{shot}-{theme}.png").expanduser().resolve()
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_page = pathlib.Path(tmp) / page_p.name
                    tmp_page.write_text(themed)
                    if width < 600:
                        # Headless Chrome won't lay out narrower than about 500px, so a phone-width
                        # check renders the page inside an iframe of exactly that width.
                        frame = pathlib.Path(tmp) / "_frame.html"
                        frame.write_text(f'<!doctype html><body style="margin:0"><iframe src="{tmp_page.name}" '
                                         f'style="border:0;width:{width}px;height:2400px;display:block"></iframe>')
                        tmp_page = frame
                    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
                                    f"--user-data-dir={tmp}/profile", "--virtual-time-budget=3000",
                                    f"--window-size={width},2400", f"--screenshot={out}", tmp_page.as_uri()],
                                   capture_output=True, timeout=90)
                print(f"screenshot: {out}" if out.exists() else f"screenshot failed for the {theme} theme")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
