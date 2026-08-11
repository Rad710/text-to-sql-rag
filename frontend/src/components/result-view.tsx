import { lazy, Suspense, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { analyzeResult, formatCellValue, parseNumeric } from "@/lib/chart-data";

import { cn } from "@/lib/utils";

// Recharts is ~900 kB; the chart is opt-in behind the toggle, so defer the whole module until the user
// first switches to Gráfico. Keeps it out of the initial bundle.
const ResultChart = lazy(() => import("@/components/result-chart"));

/** Structured result carried on the `run_sql` tool-call part (decision 0006). */
export type SqlResult = {
  columns: string[];
  rows: string[][];
  rowCount: number;
  truncated: boolean;
};

export function isSqlResult(value: unknown): value is SqlResult {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return Array.isArray(v.columns) && Array.isArray(v.rows);
}

/** The query result as a real table from structured rows — the payoff of decision 0005/0006. */
function ResultTable({ columns, rows }: SqlResult) {
  return (
    <table className="my-1 w-full border-separate border-spacing-0 text-sm">
      <thead>
        <tr>
          {columns.map((col) => (
            <th
              key={col}
              className="bg-muted border-muted-foreground/20 border-b px-3 py-1.5 text-start font-medium first:rounded-ss-md last:rounded-se-md"
            >
              {col}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, r) => (
          // Static, read-only result grid — rows never reorder, so the row index is a stable key.
          // biome-ignore lint/suspicious/noArrayIndexKey: positional result rows, no natural id
          <tr key={r}>
            {row.map((cell, c) => {
              const numeric = parseNumeric(cell) !== null;
              return (
                <td
                  key={columns[c]}
                  className={cn(
                    "border-muted-foreground/20 border-b border-s px-3 py-1.5 last:border-e",
                    // Right-align + tabular figures so numeric columns line up.
                    numeric && "text-end tabular-nums",
                  )}
                >
                  {formatCellValue(cell)}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type View = "table" | "chart";

/** Small segmented Tabla/Gráfico switch — only rendered when a chart actually fits. */
function ViewToggle({ view, onChange }: { view: View; onChange: (v: View) => void }) {
  return (
    <div className="mb-1 inline-flex gap-0.5 rounded-lg bg-muted p-0.5" data-slot="button-group">
      <Button
        size="xs"
        variant={view === "table" ? "outline" : "ghost"}
        aria-pressed={view === "table"}
        onClick={() => onChange("table")}
      >
        Tabla
      </Button>
      <Button
        size="xs"
        variant={view === "chart" ? "outline" : "ghost"}
        aria-pressed={view === "chart"}
        onClick={() => onChange("chart")}
      >
        Gráfico
      </Button>
    </div>
  );
}

/**
 * Owns the result presentation: always a table, plus a Tabla/Gráfico toggle and a chart when the shape
 * fits (one label column + numeric column(s), 2..50 rows — see analyzeResult). Table is the default view.
 */
export function ResultView(result: SqlResult) {
  const spec = useMemo(
    () => analyzeResult(result.columns, result.rows),
    [result.columns, result.rows],
  );
  const [view, setView] = useState<View>("table");
  const showChart = spec !== null && view === "chart";

  return (
    <div className="aui-sql-result overflow-x-auto">
      {spec ? <ViewToggle view={view} onChange={setView} /> : null}
      {showChart ? (
        <Suspense
          fallback={
            <div className="text-muted-foreground my-2 h-64 text-xs">Cargando gráfico…</div>
          }
        >
          <ResultChart spec={spec} />
        </Suspense>
      ) : (
        <ResultTable {...result} />
      )}
      <p className="text-muted-foreground mt-1 text-xs">
        {result.rowCount} {result.rowCount === 1 ? "row" : "rows"}
        {result.truncated ? ", truncated" : ""}
      </p>
    </div>
  );
}
