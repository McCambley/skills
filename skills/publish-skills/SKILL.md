---
name: publish-skills
description: Publish my local custom skills to my public GitHub skills repo, after checking them for private details.
disable-model-invocation: true
argument-hint: "[skill names to publish only these] [--dry-run]"
---

# Publish skills

Mirror the user's custom skills into their public skills repo and push. The **local skill is the source of truth**: fix everything in the local folder (`~/.claude/skills/<name>/`), then stage again. Never hand-edit the copies in the repo clone, because the next stage overwrites them.

The repo is public. A push is the point of no return: anything pushed may be cached or indexed even after it is deleted. Steps 2 and 3 exist so nothing private reaches step 5.

Settings and the exact rules for which skills count as custom are in the docstring of `scripts/publish.py`. Defaults: repo `McCambley/skills`, clone at `~/dev/<owner>-<name>`. Staging refuses a folder that is a clone of any other repo.

## 1. Stage

```sh
python3 ~/.claude/skills/publish-skills/scripts/publish.py stage
```

It clones or pulls the repo, mirrors every custom skill into `skills/<name>/` (removing skills no longer present locally), rebuilds the README's skill table from each skill's `description`, prints `git status`, and scans everything that will be published. If it says the repo doesn't exist, create it with the command it prints, then stage again.

Check the "publish" and "skip" lists with `publish.py list` when a skill is missing or unexpected. If `$ARGUMENTS` names skills, publish only those: after staging, restore every other path with `git checkout -- <path>` (and `git clean` for new ones) before committing.

**Done when** the stage exits 0 (`SCAN: clean`). Exit 2 means go to step 2.

## 2. Generalize

Read every new or changed skill in full (`git diff` in the clone, plus new files), not only the scan's hits. The scan catches patterns; you catch meaning. Make each skill useful to a stranger who has none of the user's context. Fix the **local** skill:

- **People, employers, clients, project names**: replace with neutral examples (`alex`, `sam`, "Payments Rewrite"). Keep the example's shape so it still teaches.
- **Links to claude.ai artifacts, docs, or other private resources**: a stranger can't open them. If the skill depends on what the resource holds (a design system, a template, a reference doc), **turn that resource into its own skill**: read it with the Artifact tool (or the matching connector), write a self-contained skill from its content, and change the original skill to point at the new skill by name. If a skill already holds that content, point at that skill instead and delete the duplicate copy. Keep the private link, if still useful to the user, in a `*.local.md` file beside it.
- **Machine-specific facts** (worktree slot names, local paths, account details): rewrite as configurable or as examples, or move to a `*.local.*` file.
- **Secrets**: delete from the skill. Tell the user to rotate any key that was in a file, since it may already be in git history elsewhere.
- **A false positive** (a placeholder, a public URL that only looks private): add the exact matched string to `allow.local.txt` in this skill's folder.
- **A new private term** you spotted that the scan missed (a coworker's name, a client): add it to `denylist.local.txt` in this skill's folder, so future scans catch it.

Re-run any checks a skill ships with after changing it (for example its `scripts/*.py --check`), so the local skill still works. Then stage again.

**Done when** the stage exits 0 and you have read every changed file in the diff.

## 3. Review the diff

In the clone, read `git diff --stat` and `git status --short`. Every change should trace to a local edit. Removed skills are deliberate: if a removal is a surprise, stop and ask.

If `--dry-run` was passed, stop here and report what would be published.

## 4. Commit

In the clone, commit with a message that names the skills added, changed and removed, and why if you know it (for example, "Generalize build-board examples"). Use the commit attribution the session gives.

## 5. Push

`git push`. Then report in a few lines:

- the repo URL (`https://github.com/<repo>`),
- the skills added, changed or removed,
- each generalization you made to a local skill, so the user knows their local copy changed,
- anything you moved to a `*.local.*` file or added to the allow or deny list.
