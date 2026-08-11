---
status: in-progress
updated: 2026-08-11
depends_on: [0010]
decision: null
---

# 0021 — Result charts (bar/line when the shape fits)

## Goal
When a query result has an obvious chartable shape (one label column + one or more numeric columns),
offer a **Gráfico** view alongside the existing table so a user can *see* "facturación por ruta" as bars
instead of reading a grid. Charts are opt-in per result via a small **Tabla / Gráfico** toggle; the table
stays the default. Purely a frontend render of the structured `run_sql` result we already stream
([decision 0006](../../decisions/0006-structured-results-frontend-presentation.md)) — no backend change.

## Context
The `run_sql` tool part already carries structured `{columns, rows, rowCount, truncated}` and renders a
real `<table>` in [`frontend/src/components/run-sql-tool.tsx`](../../../frontend/src/components/run-sql-tool.tsx).
Charts are the same data, drawn. Library = **Recharts 3.10.1** (React 19 peer-supported), pinned. The
chart-fit detection is pure and must be unit-tested independently of React.

Decisions (from the user, 2026-08-11):
- **Toggle** Tabla/Gráfico; table is the default view. Toggle only appears when a chart fits.
- **Auto** chart type: **line** when the label column looks temporal (date / `YYYY-MM` / year / time);
  **bar** otherwise. No manual bar/line switch.

## Fit heuristic (pure)
A result is chartable when:
- there is **≥1** non-numeric ("label") column, and
- there is **≥1** numeric column (all its values parse as numbers), and
- row count is in **[2, 50]** (a single row is a stat, not a chart; too many bars is noise).

The **category axis** is the label column; **several label columns are joined** into one composite
category (`origin · destination` → "Ciudad del Este · Asuncion") — a "por ruta" result has two
dimensions, and this plots one bar per route. Numeric columns each become a series.

Type: **line** only when there is a *single* label column and its values look temporal (`YYYY-MM`, ISO
date, or `Date.parse`-able with a date separator); a composite (multi-column) axis is categorical → **bar**.
A bare 4-digit year is a numeric column, so an "ingresos por año" shape isn't auto-detected (documented
limitation — we don't guess which of several numeric columns is the axis).

## Plan
1. `frontend/src/lib/chart-data.ts` — pure `analyzeResult(columns, rows)` → `null | { kind: "bar"|"line",
   labelKey, series: string[], data: Array<Record<string, string|number>> }`. No React/Recharts import.
2. `frontend/src/lib/chart-data.test.ts` — unit tests (vitest): bar case, temporal→line, single-row →
   null, all-text → null, >50 rows → null, multi-series, thousands/locale numeric parsing.
3. `frontend/src/components/result-view.tsx` — a `ResultView` that owns the Tabla/Gráfico toggle
   (segmented control) + the `ResultTable`, and **lazy-loads** the chart. Toggle hidden when
   `analyzeResult` returns null.
4. `frontend/src/components/result-chart.tsx` — the Recharts bar/line, a **default export** loaded via
   `React.lazy` (Recharts is ~900 kB and the chart is opt-in, so it must not bloat the initial bundle).
   Move `ResultTable` into `result-view.tsx`; `run-sql-tool.tsx` renders `<ResultView {...result} />`.
5. Extend `App.test.tsx`: after the table renders, the **Gráfico** toggle is present for the chartable
   SSE fixture and switching shows the chart (assert the Recharts SVG / series presence in jsdom).
6. Gates: `pnpm lint`, `pnpm build`, `pnpm test`; browser-verify with Playwright (bar for a by-route
   query, line for a by-month query); 0 console errors.

## Done when
- [x] Pure `analyzeResult` + unit tests cover bar, line(temporal), composite axis, and every reject case;
      `pnpm test` green (13 chart-data cases).
- [x] `run_sql` results show a **Tabla/Gráfico** toggle only when a chart fits; table is default; bar vs
      line auto-selected; multiple label columns → composite axis; multiple numeric columns → multiple series.
- [x] `pnpm lint` + `pnpm build` + `pnpm test` green (Recharts lazy-split to its own chunk); App.test.tsx
      asserts the toggle + chart round-trip.
- [x] Browser-verified: bar for "por ruta" (composite axis) + multi-series ("ingresos mensuales", legend),
      0 console errors. Line path is unit-tested (a temporal result needs a real LLM to show in-browser).
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
