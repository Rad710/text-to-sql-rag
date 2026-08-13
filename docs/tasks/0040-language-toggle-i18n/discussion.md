# 0040 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-13: **Origin.** Owner: a header ES/EN toggle next to the name instead of showing both
  languages at once; use a real React i18n lib with `t()`; auto-select the machine language on first
  load; "some API responses depend on the chrome language — check thoroughly."
- 2026-08-13: **Backend audit.** Answer language keyed off the *question* (`_detect_lang` mock; "user's
  language" prompt for the real LLM); `_FALLBACK`/`_EXHAUSTED` + the 429 `detail` were hardcoded Spanish.
  So the toggle must reach the backend to be authoritative → chosen behavior: chrome language drives the
  answer (owner confirmed), with question-detection kept as the no-language fallback for the eval harness.
- 2026-08-13: **Library.** `react-i18next` + `i18next-browser-languagedetector` (owner wanted a real lib,
  not a hand-rolled dict). Detector order localStorage→navigator, fallback `es`, `load: languageOnly`.
- 2026-08-13: **Vendored scope.** Only the two customized Spanish feedback tooltips in `thread.tsx` were
  localized (via `useTranslation`); upstream English icon-tooltips (Copy/Send/More) left as-is.
- 2026-08-13: **Tests.** Owner asked tests run in **English** — pinned `dyr_lang=en` in setup; updated
  App/runtime assertions to the English strings; added an i18n toggle test. All gates green + prod build.
