---
status: accepted
date: 2026-08-13
---

# 0014 — UI language: react-i18next, auto-detected, chrome drives the answer language

## Context
The UI showed both languages at once (bilingual welcome line, mixed-language suggestions). The owner
wants a proper **ES | EN toggle** that auto-selects the visitor's machine language on first load, using
a real i18n library (not a hand-rolled dictionary). An audit also found several **API responses are
language-dependent** — the assistant answer keyed off the *question's* language, and `_FALLBACK` /
`_EXHAUSTED` / the 429 detail were hardcoded Spanish — so a chrome toggle alone wouldn't make the app
consistently one language.

## Decision
- **`react-i18next` + `i18next-browser-languagedetector`.** Detect order `localStorage → navigator`,
  `fallbackLng: es` (domain default), `load: "languageOnly"` (so `en-US` → `en`), choice persisted under
  `dyr_lang`. A header **ES | EN** toggle calls `i18n.changeLanguage`.
- **The chrome language is authoritative for chat.** The frontend sends `language` in the `/chat` body;
  the backend threads it to the agent → LLM: the real model gets a *"write the final answer in
  {language}"* system directive, the mock uses it for its prose, and `_FALLBACK` / `_EXHAUSTED` are
  localized. When absent (e.g. the eval harness), the backend falls back to detecting the question's
  language — backward-compatible.
- **Client owns user-facing chat messages** (session-expired, rate-limit) via `i18n.t`, so we no longer
  depend on the backend's Spanish 429 `detail`.
- **Vendored primitives:** only the two project-customized Spanish tooltips (feedback 👍/👎) are
  localized; upstream English icon-tooltips (Copy, Send, More…) are left as-is.

## Consequences
- Good: one deterministic language across chrome **and** answers; auto-detected first load; the decision
  layer (backend answer-language) is explicit and tested.
- Cost: two runtime dependencies; `/chat` gains an optional `language` field (contract change, defaulted).
- Accepted: a few upstream vendored icon-tooltips remain English regardless of toggle (minor, hover-only).

## Alternatives considered
- **Hand-rolled `t()` + dictionary (no dep)** — rejected: the owner asked for a real library; i18next
  gives detection, pluralization, and interpolation for free.
- **Toggle = UI chrome only, answers keyed to the question** — rejected: the toggle should be
  authoritative, so an EN user gets EN answers even when typing Spanish.
