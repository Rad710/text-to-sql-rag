# 0021 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Kickoff. User decided (via consult): **toggle** Tabla/Gráfico with table as default view,
  and **auto** chart type — line when the label column is temporal, bar otherwise. No manual bar/line
  switch (kept controls minimal). Library = **Recharts 3.10.1**; confirmed React 19 in its peer range
  (`^19.0.0`) and pinned exact. Recharts drags in a sizeable transitive tree (redux-toolkit, victory-vendor
  d3 modules) — acceptable, it's the charting lib we chose in the feature scoping.
- 2026-08-11: Design — keep the fit detection **pure** (`lib/chart-data.ts`, no React/Recharts) so it
  unit-tests without a DOM, mirroring the backend pure/impure split. Heuristic: exactly one non-numeric
  label column + ≥1 numeric column + 2..50 rows. This deliberately excludes single-row scalar answers
  (a stat, not a chart) and very wide results (noise). Numeric parse tolerates thousands separators.
- 2026-08-11: Built + verified. `lib/chart-data.ts` (`analyzeResult` + `parseNumeric`) 100% pure, 13
  unit cases. `components/result-view.tsx` owns the Tabla/Gráfico toggle + table and `React.lazy`-loads
  `components/result-chart.tsx` (Recharts) — the chart split into its own 386 kB chunk so it stays out of
  the initial bundle (chart is opt-in). `run-sql-tool.tsx` now renders `<ResultView>`.
- 2026-08-11: **Heuristic gap found during browser QA** — the mock's "facturación por ruta" returns
  `origin, destination, revenue` (TWO label columns), which the original "exactly one label column" rule
  rejected → no chart. A route is genuinely two-dimensional, so generalised the rule: **≥1** label column,
  joined into one composite category (`origin · destination`), numeric columns as series. Line stays
  reserved for a single temporal label column. Updated tests accordingly (the old "reject: >1 label
  column" test became "composite axis: several label columns join into one bar category").
- 2026-08-11: Browser-verified end-to-end (throwaway Postgres :55432 + MySQL + mock LLM): "por ruta" →
  4-bar descending bar chart with composite route labels; "ingresos mensuales" → composite axis + 2 series
  (revenue/trips) with a legend. Toggle works, table is the default view, 0 console errors. (The one console
  warning is a pre-existing Base UI collapsible CSS note, unrelated.) Line/temporal path is covered by unit
  tests only — the deterministic mock never emits a temporal column, so showing a line in-browser needs a
  real LLM (task 0015 wiring). Gates: pnpm lint + build + test all green.
