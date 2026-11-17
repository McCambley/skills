# Skills

My agent skills for Claude Code and other agents that read `SKILL.md` files.

## Skills

<!-- skills:start -->
| Skill | What it does |
| --- | --- |
| [`build-board`](skills/build-board/SKILL.md) | Turn a development plan into a live, shared build board on claude.ai. |
| [`go-crazy`](skills/go-crazy/SKILL.md) | Take a plan or build board and fan out background agents on every task that is ready for one assignee, following the plan's "For agents" protocol. |
| [`iso-plain-language`](skills/iso-plain-language/SKILL.md) | Write human-facing text in plain language that follows ISO 24495-1:2023. |
| [`linear-design-system`](skills/linear-design-system/SKILL.md) | Style pages, artifacts, apps and other UI with Vector, the user's own design system in the style of linear.app. |
| [`publish-skills`](skills/publish-skills/SKILL.md) | Publish my local custom skills to my public GitHub skills repo, after checking them for private details. |
<!-- skills:end -->

## Install

With the [skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills@latest add McCambley/skills            # pick skills interactively
npx skills@latest add McCambley/skills -s <name>  # one skill
```

Or copy a folder from `skills/` into `~/.claude/skills/` (or your agent's skills folder).

Some skills use others. When a skill says it needs another one, install both.

## How this repo is updated

The `publish-skills` skill copies my local skills here, checks them for private details, and pushes.
Edit skills locally, not in this repo: the next publish overwrites the copies here.
