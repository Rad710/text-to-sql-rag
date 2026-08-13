---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-13     # YYYY-MM-DD, last touched
decision: 0014          # decisions/NNNN that governs this task, if any
depends_on: []          # task numbers that must finish first
---

# 0040 — Language toggle + i18n (ES/EN), chrome drives the answer language

## Goal
Replace the "both languages at once" UI with an **ES | EN** toggle in the header (next to the user
name) that auto-selects the visitor's machine language on first load. Use a real i18n library. The
toggle is authoritative: it localizes the UI **and** the assistant's answers.

## Context
Owner request; a backend audit ([decision 0014](../../decisions/0014-ui-language-i18n.md)) found the
answer language keyed off the *question*, with `_FALLBACK`/`_EXHAUSTED`/429-detail hardcoded Spanish —
so the toggle has to reach the backend to be consistent.

## Plan
- **Frontend:** `react-i18next` + `i18next-browser-languagedetector`; `src/i18n/` (config + `es`/`en`
  resources); `t()` across all app chrome (header, Welcome + suggestions, login, sidebar, ResultView,
  runtime messages) + the two customized feedback tooltips in `thread.tsx`; a `LanguageToggle` in the
  header; send `language` in the `/chat` body.
- **Backend:** `/chat` accepts optional `language`; thread it through `stream`/`answer_question` → the
  system-prompt directive (real LLM) and `complete(language=…)` (mock); localize `_FALLBACK`/`_EXHAUSTED`;
  fall back to question-detection when absent.

## Done when
- [x] Header ES|EN toggle; first load auto-detects the machine language, choice persisted.
- [x] All app-owned UI strings localized (no bilingual "both at once"); suggestions per language.
- [x] `/chat` carries `language`; it drives the answer + fallback/exhausted language (mock + real LLM).
- [x] Client-side chat messages (session/rate-limit) localized; no reliance on the backend 429 detail.
- [x] Tests run in English; toggle test added. Gates green: backend ruff/mypy/pytest; frontend
      biome/tsc/vitest + production build.
