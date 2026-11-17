---
name: go-crazy
description: Take a plan or build board and fan out background agents on every task that is ready for one assignee, following the plan's "For agents" protocol. Keeps dispatching as agents finish and tasks unblock, and when nothing can move, sets a timer to check back. Use when the user says /go-crazy, "fan out agents", "swarm the board", "go crazy", "run the ready tasks in parallel", or "keep agents going on my lane".
argument-hint: "[plan-or-board-url] [--assignee <person-id>] [--max <n>] [--every <minutes>]"
---

# Go crazy

Run one assignee's share of a plan with parallel background agents. You are the **orchestrator**: you pick
tasks, start workers, check their results, and keep going until the assignee's agent work is done or only
human decisions are left. Workers do the tasks; you never do a task's work yourself while running this skill.

## Inputs

Parse `$ARGUMENTS`:

| Input | Default |
| --- | --- |
| Plan: a claude.ai build-board URL, a Claude Doc, or a local Markdown plan | The board or plan named in memory or `CLAUDE.md` for the current project |
| `--assignee` | The only person on the plan. If there are several, ask once. |
| `--max` | The number of agent slots the project has (see "Workspaces"), otherwise 4 |
| `--every` | 45 minutes between check-backs when stuck |

If you can't find a plan, stop and ask for one. Don't invent tasks.

## 1. Load the contract

Read all of it before dispatching anything.

- **Build board** (made by the `build-board` skill): load `ArtifactData` with ToolSearch. `get meta/plan`,
  `get meta/rules`, `get meta/humans`, `get meta/standing`, `list tasks` (limit 1000), and query `log`
  (latest 30 by `ts`). Read the page's
  **"For agents"** section with the Artifact tool (`action: "read"`). That protocol and the rules are what
  every worker must follow.
- **Markdown or Doc plan**: read it in full. Take tasks, assignees, dependencies and status from it. If it
  has no machine-readable status, keep the status in the ledger (step 3) and tell the user.
- **Project agent brief**: check memory and `CLAUDE.md` for a worker brief (for example
  `AGENT_BRIEF.md`) and for workspace slots. A brief written for this project beats a generic prompt.
  Use it word for word, filling in its placeholders.

## 2. Find the work

Sort the assignee's tasks into these groups:

- **Ready**: status `todo`, in the assignee's *agent* lane, and every dep is `done`.
- **Resume**: `in_progress` or `review`, owned by the assignee, with no worker of yours running on it
  (for example, left over from an earlier session or a stopped agent). These go before Ready tasks.
- **Human only**: decision, approval or gate tasks. That means a lane meant for the person themself (such
  as `<person>-calls`), a task whose `needs` names a person, access or a decision, or anything the rules
  say agents never close. **Never dispatch these.** List them for the user.
- **Waiting**: everything else, with the dep or `needs` it is waiting on.

Then check for clashes before dispatching ready tasks together:

- If the rules limit something to one open PR at a time (for example migrations), start only one task
  that needs it.
- Don't run two tasks at once that edit the same file or contract, if their specs say so.
- Prefer tasks on the critical path and tasks that unblock the most others.

## 3. Keep a ledger

Write `~/.claude/go-crazy/<plan-slug>.json` and update it on every change, so the run survives context
compaction and a new session can pick it up. It holds the plan URL or path, the assignee, `max`, and
one entry per worker: task ID, agent name, workspace, start time and last known status. The board stays
the source of truth for task status. The ledger only records which worker owns which workspace.

On start, read any existing ledger. Check its workers with `ListAgents`, and treat any that are gone as
Resume candidates.

## 4. Workspaces

Each worker needs its own checkout.

- If the project has prepared slots (memory or `CLAUDE.md` will say, for example `s1`–`s5` worktrees
  plus a setup script), give each worker a free slot. Track which are taken in the ledger. Run the
  setup script for a slot that doesn't exist yet. `--max` defaults to the number of slots.
- Otherwise start the agent with `isolation: "worktree"`.

Never give two workers the same workspace. Never point a worker at the user's own checkout.

## 5. Dispatch

Start up to `max − running` workers, one task each, in a **single message** with several `Agent` calls:

- `run_in_background: true` and `subagent_type: "general-purpose"` (or the type the project names)
- `description`: `"<TASK-ID> <short title>"`
- `prompt`: the project brief with `{TASK}`, `{SLOT}` and the other placeholders filled in. With no
  project brief, build the prompt from the template below.

Every prompt must say plainly **whose work it is**. Include this, with the names filled in:

> You are working on **<Assignee>'s** item. Claim it as `owner: "<person-id>"` in lane `<lane>`, and
> write every log entry with `lane: "<lane>"`. <Assignee> started you in the background and can't
> answer questions while you work. Don't wait for approval. If you're truly blocked, set the task to
> `blocked` with a reason, log it, and stop. Never close or decide a task in a human-only lane.

For a Resume task, add: "You are resuming. Don't claim it again. Follow the resuming steps."

### Prompt template (when the project has no brief)

```
You are a worker agent on <plan title> for <Assignee> (person id `<id>`, lane `<lane>`).
<the "whose work it is" paragraph above>

Your task: <TASK-ID>, <title>
Your workspace: <path or "the isolated worktree you were started in">. Work only there.

Board: <url>. Read and write it with ArtifactData (load it with ToolSearch "select:ArtifactData").
Follow the board's "For agents" protocol exactly. It is copied here:
<the protocol text, verbatim>

Project rules (these override everything else):
<meta/rules, verbatim>

Checkpoints: commit work in progress to your branch after each meaningful step, and keep
impl.summary current as "Done so far: ... Next: ...", so another agent can resume if you stop.

Final message (to the orchestrator, under 250 words): the task's final board status, the PR URL
and whether it merged, what you verified, anything waiting on <Assignee>, and follow-ups other
tasks should know about.
```

After dispatching, tell the user in one short line per task: ID, title, workspace.

## 6. When a worker finishes

You're notified automatically. Don't poll. Then:

1. **Check the board**, not just the report. `get tasks/<ID>` and confirm the status the worker claimed.
   If the report says done but the board doesn't, or the PR isn't merged, say so to the user plainly.
2. Free its workspace in the ledger.
3. Give the user a short update: task, outcome, PR, anything waiting on them.
4. If the worker stopped part-way (usage limit, crash, or no final status), the task becomes a Resume
   candidate. Retry each task at most twice. After that, mark it for the user and move on.
5. **Recompute the work** (step 2) and dispatch into the free capacity (step 5).
6. **Update the human sections** (below).

## Keep the human sections current

A build board has two sections written for people: **"For humans"** (`meta/humans`), which says exactly
what people must do so agents can continue, and **"Where we stand"** (`meta/standing`), which compares the
project with its final goal. The orchestrator owns both, so the user never has to ask "what do I need to
do?". Field shapes are under "Keeping the human sections current" in the page's "For agents" section.

- **When:** after every worker finishes, after the user gives a decision or does something on the list,
  when you start or stop being stuck, and before you answer "what's waiting on me?". Workers also update
  them, so always `get` first and `update` with `if_version`, writing whole arrays back.
- **For humans:** one item per thing only a person can do, with numbered steps that say exactly where to
  go and what to click or run, how long it takes, and what it unblocks. Check the facts in the item (the
  right run, the right page, the current count) before you write it. Blocking items get `blocking: true`;
  scheduled reviews and other non-blocking items get `false`. Remove an item when the board or the user
  shows it is done. Never record a decision for the user.
- **Where we stand:** keep `summary`, `parts`, `recent`, `next` and `risks` true. Say plainly whether the
  deadline still holds.
- Write both in plain language (ISO 24495-1). Load the `iso-plain-language` skill if it's available.
- When you tell the user what's waiting on them, give the same content as "For humans" and point them at
  the section on the board, so they can look there next time instead of asking.
- On a board that doesn't have these sections yet, say so and offer to add them with the `build-board`
  skill ("Changing a live board").

## 7. When nothing can move

You're stuck when no worker is running and nothing is Ready or Resume. Then:

1. Update "For humans" and "Where we stand" first. Then tell the user what's holding things up, in a short
   list that matches "For humans". Put the human-only tasks first, since only they can clear those. Then
   the outside `needs`, and PRs waiting on CI or review.
2. Set a timer to check back:
   - Running under `/loop` (you have `ScheduleWakeup`): call it with `delaySeconds` of `--every`, and
     pass back the same `/loop` prompt.
   - Otherwise: `CronCreate` a one-shot (`recurring: false`) about `--every` minutes from now. Pick an
     off-minute (not :00 or :30) and use the prompt `/go-crazy <the same arguments>`. Give the user the
     run time from the tool's result, and say that the timer only fires while this session is open.
3. When the timer fires, start again from step 1. If nothing has changed, set the next timer and say so
   in one line. Don't repeat the whole blocked list.

While workers are running you don't need a timer, since their completion wakes you. If you're running
under `/loop`, still set a long fallback wakeup (about 30 minutes) in case a worker hangs.

## 8. Stop

Stop, and don't set another timer, when:

- every task in the assignee's agent lane is `done`, or
- only human-only tasks are left, and no other task is waiting on anything an agent could do.

Then update "For humans" and "Where we stand", and give a final summary: tasks done this run, with their
PRs, what's waiting on the user (as in "For humans"), and any follow-ups. Use `PushNotification` if the user has probably walked away. Delete the ledger only when all
of the assignee's tasks are done.

## Rules for the orchestrator

- Never claim, close or decide a human-only task, and never record a decision for the user.
- Never edit `meta/plan` or `meta/rules`, and never re-seed board documents.
- Don't change a task's scope to make it dispatchable. Report it instead.
- Respect the project's machine limits (for example a cap on concurrent compose stacks). Lower `max` if
  the project brief or memory says the machine can't take more.
- Approvals still apply. If a worker reports that something needs the user (a key, a merge permission,
  outside contact), pass it on. Don't route around it.
- Report faithfully. Never say a task is done unless the board says so.
