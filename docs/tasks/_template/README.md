<!--
HOW TO USE
  Copy this whole folder to ../NNNN-short-slug/ (zero-padded, next free number) and fill in.

STRUCTURE (strict — every task is exactly this)
  NNNN-slug/
    README.md      ← THIS FILE: the spec. Sections below; Goal/Plan/Done-when REQUIRED.
    discussion.md  ← append-only, dated log of decisions / options weighed / dead ends. Required.
    research.md    ← findings + evidence behind the spec. OPTIONAL — only if the task needed digging.

RULES
  - `status` in the frontmatter is the source of truth; keep it in sync with the backlog table.
  - "Done when" MUST be checkable acceptance criteria. The task is done ONLY when every box passes.
  - One task `in-progress` at a time (see ../README.md and CLAUDE.md). Don't touch other tasks.
  - Link into reference/decisions — never copy facts (single source of truth).
  - Trivial task with no real trade-offs? Goal + Plan + Done-when is enough; skip Context/research.
-->
---
status: proposed        # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-10     # YYYY-MM-DD, last touched
depends_on: []          # task numbers that must finish first, e.g. [0002]
decision: null          # decisions/NNNN that governs this task, if any
---

# NNNN — <plain-language title, no jargon>

## Goal
*(required)* What ships and why it matters — one short paragraph a non-expert understands.

## Context
*(required unless trivial)* Links — never copies — into decisions / reference for the "why" and the
current code. Prerequisites. If the task needed real investigation, put it in `research.md` and point here.

## Plan
*(required)* Concrete, ordered steps. Name the exact files touched.

## Done when
*(required)* The definition of done.
- [ ] Checkable acceptance criteria — the task is done ONLY when every box is ticked.

---
Log → [`discussion.md`](discussion.md) · findings (if any) → `research.md`
