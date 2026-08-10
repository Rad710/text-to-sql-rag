# Documentation index

A **text-to-SQL RAG assistant** over the synthetic *DYR Transportes* freight schema: natural-language
question → RAG-retrieved schema → read-only SQL → plain-language answer, driven by a bounded agentic
tool-loop. See [`../CLAUDE.md`](../CLAUDE.md) for the one-paragraph overview.

This file is only a **map**. Each fact lives in exactly one place below; nothing here is restated, so
nothing here goes stale.

## Where things live

| You want… | Go to |
|---|---|
| **What to work on next** (the backlog) | [`tasks/README.md`](tasks/README.md) |
| **Why we chose X** (decisions) | [`decisions/README.md`](decisions/README.md) |
| **How the system is designed** (architecture) | [`architecture.md`](architecture.md) |
| **Reference facts** (the DB schema, constants, table/column names) | [`reference.md`](reference.md) |
| **How this repo was built with AI** (for readers/recruiters) | [`ai-workflow.md`](ai-workflow.md) |

## How we work (strict)

- **One task in progress at a time.** Exactly one task in [`tasks/`](tasks/) is `in-progress`; finish it
  to its "Done when" checklist before starting the next. No "while I'm here."
- **Each task is a folder** (`tasks/NNNN-slug/`): `README.md` is the spec, `discussion.md` the running
  log, `research.md` optional. Copy [`tasks/_template/`](tasks/_template/) to start one.
- **Decisions are immutable:** never rewrite an accepted decision — supersede it with a new numbered
  record that links back.
- **Reference facts have one home** ([`reference.md`](reference.md)); everything else links to it.
- **This folder is the only context store.** There is no `HANDOFF.md` — the in-progress task row in
  [`tasks/README.md`](tasks/README.md) *is* the cross-session pointer, and every non-obvious concern goes
  in that task's `discussion.md`.
- **Commit per task, in small batches** — see [`ai-workflow.md`](ai-workflow.md).

## Cold-starting a session

A fresh agent (or you, after `/clear`) gets fully up to speed by reading in this order — no other context
needed:

1. **This file** (the map).
2. [`tasks/README.md`](tasks/README.md) → find the single `in-progress` row. That is the task.
3. That task's folder: **`README.md`** (Goal · Context · Plan · Done when), then **`discussion.md`**.
4. Follow the task's **Context links** — [`decisions/`](decisions/README.md),
   [`reference.md`](reference.md), [`architecture.md`](architecture.md) — for the "why" and the current
   facts. These are the single source of truth; the task never restates them.
5. Work to the "Done when" checklist; log decisions in `discussion.md` as you go. When every box passes,
   set `status: done` in the task frontmatter **and** the backlog row, then pick the next.

To cold-start, point the agent here: *"Read `docs/README.md` and continue the in-progress task."*
