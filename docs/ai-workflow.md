# How this repo was built (AI-assisted workflow)

This project was built with **Claude Code** as a pair-programmer, using a deliberate, auditable workflow.
The point of this page: the AI didn't "generate the repo" in one shot — it was driven through small,
reviewed, test-backed steps, and the paper trail is committed so you can see exactly how.

## The workflow

- **Everything is a task.** Work is broken into numbered, self-contained task folders under
  [`tasks/`](tasks/) — each with a spec (`README.md`: Goal · Context · Plan · Done when) and an append-only
  `discussion.md` log. The backlog and build order live in [`tasks/README.md`](tasks/README.md).
- **One task in progress at a time.** No "while I'm here" changes; a task is done only when every "Done
  when" box passes (and that means tests actually run and pass, not "should work").
- **Decisions are recorded and immutable.** Design choices (stack, agentic-vs-pipeline, SQL safety) are
  written down as numbered records in [`decisions/`](decisions/README.md) with the alternatives considered.
  A reversed decision is *superseded* by a new record, never edited away — so the reasoning history stays
  intact.
- **Reference facts have one home.** The schema and constants live in [`reference.md`](reference.md);
  nothing else restates them, so nothing drifts.
- **Commit per task, in small batches.** Each task is a branch with focused commits — never one giant
  "did everything" commit. The commit history is meant to be read.

## Why it's public

The `docs/` tree is committed on purpose. For a reviewer, it's the honest answer to "how do you use AI?":
disciplined, test-backed, decision-logged, and reviewable — the opposite of an opaque one-prompt dump. The
process is part of the portfolio, not scaffolding to hide.

## Clean-room note

The design was informed by two private reference implementations, but this repo is a **clean-room build**:
no data, prompts, credentials, or client-specific logic were copied. The database is synthetic and the
patterns were re-implemented from scratch against the public schema.
