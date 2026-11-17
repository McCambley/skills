#!/usr/bin/env python3
"""Stage local custom skills into a git clone of the public skills repo, and scan them for private details.

Usage:
  python3 publish.py stage    Clone or pull the repo, mirror custom skills into skills/, rebuild the
                              README table, scan what will be published, print git status.
  python3 publish.py scan     Scan the local custom skills only. Changes nothing.
  python3 publish.py list     Print the custom skills that would be published, and why others are skipped.

Exit codes: 0 clean, 2 the scan found something to fix, 1 any other error.
It never commits or pushes. The agent does that after reviewing the result.

Settings (environment variables):
  SKILLS_REPO      GitHub repo to publish to            default McCambley/skills
  SKILLS_REPO_DIR  Local clone of that repo             default ~/dev/<owner>-<name>
                   Staging refuses a folder whose origin is a different repo.
  SKILLS_SOURCES   Colon-separated skill folders        default ~/.claude/skills:~/.agents/skills

What counts as a custom skill: a real folder (not a symlink) with a SKILL.md, in one of the source
folders, that is not
  - installed from somewhere else (listed in ~/.agents/.skill-lock.json),
  - the claude.ai sync folder (`synced`),
  - named in this skill's ignore.txt.

Never published: files or folders named *.local.* or *.local, __pycache__, *.pyc, .DS_Store,
node_modules, .git.

Private terms: put one word or phrase per line in this skill's denylist.local.txt (names of people,
employers, clients, project code names). Lines in allow.local.txt are exact strings the scan ignores.
Both files stay on this machine.
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

HOME = pathlib.Path.home()
HERE = pathlib.Path(__file__).resolve().parent.parent
REPO = os.environ.get("SKILLS_REPO", "McCambley/skills")
REPO_DIR = pathlib.Path(os.environ.get("SKILLS_REPO_DIR", HOME / "dev" / REPO.lower().replace("/", "-"))).expanduser()
SOURCES = [pathlib.Path(p).expanduser() for p in
           os.environ.get("SKILLS_SOURCES", "~/.claude/skills:~/.agents/skills").split(":") if p]
LOCK = HOME / ".agents" / ".skill-lock.json"
SKIP_DIRS = {"synced"}
EXCLUDE_NAMES = {"__pycache__", ".DS_Store", "node_modules", ".git"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".sh", ".js", ".ts", ".json", ".html", ".css", ".svg", ".yml",
                 ".yaml", ".toml", ".csv", ".xml", ""}

# Strings that look private but are fine to publish (placeholders used in examples, the repo itself).
DEFAULT_ALLOW = [
    "https://claude.ai/artifact/<id>",
    "https://claude.ai/artifact/AbC123",
    "noreply@anthropic.com",
    "github.com/" + REPO,
    REPO,
]

PATTERNS = [
    ("email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+\w")),
    ("home-folder path", re.compile(r"/(?:Users|home)/(?!<)[A-Za-z0-9._-]+")),
    ("claude.ai artifact or project link", re.compile(r"claude\.ai/(?:code/)?(?:artifact|project|chat)s?/[A-Za-z0-9_-]{6,}")),
    ("share key", re.compile(r"[?&]sk=[A-Za-z0-9_-]+")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("Anthropic or OpenAI key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("internal link", re.compile(r"https?://[\w.-]*(?:atlassian\.net|slack\.com/archives|notion\.so|docs\.google\.com|linear\.app/[\w-]+/issue)[^\s)\"'`]*")),
]


def read_lines(path):
    if not path.is_file():
        return []
    return [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")]


def is_excluded(p):
    return p.name in EXCLUDE_NAMES or p.suffix == ".pyc" or ".local." in p.name or p.name.endswith(".local")


def frontmatter(skill_md):
    text = skill_md.read_text()
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if v and not line.startswith(" "):
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def discover(verbose=False):
    installed = set()
    if LOCK.is_file():
        installed = set(json.loads(LOCK.read_text()).get("skills", {}))
    ignored = set(read_lines(HERE / "ignore.txt"))
    found, notes = {}, []
    for src in SOURCES:
        if not src.is_dir():
            continue
        for d in sorted(src.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            why = None
            if d.is_symlink():
                why = "symlink (installed or managed elsewhere)"
            elif d.name in SKIP_DIRS:
                why = "claude.ai sync folder"
            elif not (d / "SKILL.md").is_file():
                why = "no SKILL.md"
            elif d.name in installed:
                why = "installed from another repo (.skill-lock.json)"
            elif d.name in ignored:
                why = "listed in ignore.txt"
            elif d.name in found:
                why = f"duplicate of {found[d.name]}"
            if why:
                notes.append(f"skip  {d}  ({why})")
            else:
                found[d.name] = d
    if verbose:
        for n, d in found.items():
            print(f"publish  {n}  ({d})")
        for n in notes:
            print(n)
    return found


def files_of(skill_dir):
    for root, dirs, files in os.walk(skill_dir):
        rootp = pathlib.Path(root)
        dirs[:] = sorted(x for x in dirs if not is_excluded(rootp / x))
        for f in sorted(files):
            p = rootp / f
            if not is_excluded(p):
                yield p


def scan(paths_by_label):
    deny = read_lines(HERE / "denylist.local.txt")
    allow = DEFAULT_ALLOW + read_lines(HERE / "allow.local.txt")
    deny_re = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in deny) + r")\b", re.I) if deny else None
    findings = []
    for label, path in paths_by_label:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            clean = line
            for a in allow:
                clean = clean.replace(a, "")
            hits = [(kind, m.group(0)) for kind, rx in PATTERNS for m in rx.finditer(clean)]
            if deny_re:
                hits += [("private term", m.group(0)) for m in deny_re.finditer(clean)]
            for kind, s in hits:
                findings.append(f"{label}:{n}: {kind}: {s[:80]}")
    return findings


def git(*args, cwd=REPO_DIR, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, text=True, capture_output=True).stdout


def origin_matches():
    url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=REPO_DIR, text=True,
                         capture_output=True).stdout.strip().lower()
    url = re.sub(r"\.git$", "", url)
    return url.endswith("/" + REPO.lower()) or url.endswith(":" + REPO.lower())


def ensure_clone():
    if REPO_DIR.exists() and not (REPO_DIR / ".git").is_dir():
        sys.exit(f"{REPO_DIR} exists but isn't a git clone. Set SKILLS_REPO_DIR to another folder.")
    if (REPO_DIR / ".git").is_dir() and not origin_matches():
        sys.exit(f"{REPO_DIR} is a clone of a different repo, not {REPO}. Leaving it alone.\n"
                 "Set SKILLS_REPO_DIR to another folder.")
    if (REPO_DIR / ".git").is_dir():
        if git("status", "--porcelain").strip():
            print(f"note: {REPO_DIR} had uncommitted changes before staging; they are kept.")
        if git("remote", check=False).strip():
            subprocess.run(["git", "pull", "--ff-only", "--quiet"], cwd=REPO_DIR, check=False)
        return
    exists = subprocess.run(["gh", "repo", "view", REPO], capture_output=True).returncode == 0
    if not exists:
        sys.exit(f"The repo {REPO} doesn't exist yet. Create it first:\n"
                 f"  gh repo create {REPO} --public --description 'My agent skills'")
    REPO_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["gh", "repo", "clone", REPO, str(REPO_DIR)], check=True)


def mirror(skills):
    dest_root = REPO_DIR / "skills"
    dest_root.mkdir(exist_ok=True)
    removed = []
    for d in sorted(dest_root.iterdir()):
        if d.is_dir() and d.name not in skills:
            shutil.rmtree(d)
            removed.append(d.name)
    for name, src in skills.items():
        dest = dest_root / name
        if dest.exists():
            shutil.rmtree(dest)
        for f in files_of(src):
            out = dest / f.relative_to(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f.resolve(), out)
    return removed


README_TEMPLATE = """# Skills

My agent skills for Claude Code and other agents that read `SKILL.md` files.

## Skills

<!-- skills:start -->
<!-- skills:end -->

## Install

With the [skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills@latest add {repo}            # pick skills interactively
npx skills@latest add {repo} -s <name>  # one skill
```

Or copy a folder from `skills/` into `~/.claude/skills/` (or your agent's skills folder).

Some skills use others. When a skill says it needs another one, install both.

## How this repo is updated

The `publish-skills` skill copies my local skills here, checks them for private details, and pushes.
Edit skills locally, not in this repo: the next publish overwrites the copies here.
"""


def first_sentence(text):
    m = re.match(r"(.+?\.)(?:\s|$)", text)
    return (m.group(1) if m else text).replace("|", "\\|")


def build_readme(skills):
    path = REPO_DIR / "README.md"
    text = path.read_text() if path.is_file() else README_TEMPLATE.format(repo=REPO)
    rows = ["| Skill | What it does |", "| --- | --- |"]
    for name in sorted(skills):
        fm = frontmatter(skills[name] / "SKILL.md")
        rows.append(f"| [`{name}`](skills/{name}/SKILL.md) | {first_sentence(fm.get('description', ''))} |")
    block = "<!-- skills:start -->\n" + "\n".join(rows) + "\n<!-- skills:end -->"
    if "<!-- skills:start -->" not in text:
        text = text.rstrip() + "\n\n## Skills\n\n" + block + "\n"
    else:
        text = re.sub(r"<!-- skills:start -->.*?<!-- skills:end -->", lambda _: block, text, flags=re.S)
    path.write_text(text)
    gi = REPO_DIR / ".gitignore"
    if not gi.is_file():
        gi.write_text(".DS_Store\n__pycache__/\n*.pyc\n*.local.*\n*.local\n")


def report(findings):
    if findings:
        print(f"\nSCAN: {len(findings)} possible private details. Fix each in the LOCAL skill, then stage again:")
        for f in findings:
            print("  " + f)
        return 2
    print("\nSCAN: clean")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stage"
    if cmd == "list":
        discover(verbose=True)
        return 0
    skills = discover()
    if not skills:
        sys.exit("No custom skills found.")
    if cmd == "scan":
        return report(scan([(f"{s}/{f.relative_to(d)}", f) for s, d in skills.items() for f in files_of(d)]))
    if cmd != "stage":
        sys.exit(__doc__)
    ensure_clone()
    removed = mirror(skills)
    build_readme(skills)
    print(f"Staged {len(skills)} skills into {REPO_DIR}: {', '.join(sorted(skills))}")
    if removed:
        print(f"Removed from the repo (no longer local): {', '.join(removed)}")
    print("\n" + (git("status", "--short") or "No changes to publish.\n").rstrip())
    staged = [(str(p.relative_to(REPO_DIR)), p) for p in sorted(REPO_DIR.rglob("*"))
              if p.is_file() and ".git" not in p.relative_to(REPO_DIR).parts]
    return report(scan(staged))


if __name__ == "__main__":
    sys.exit(main())
