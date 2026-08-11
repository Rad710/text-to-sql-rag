// Pure chart-fit detection for a structured `run_sql` result. No React / Recharts import — this is the
// decision layer, unit-tested without a DOM (mirrors the backend's pure/impure split). Given the raw
// `{columns, rows}` we already stream (decision 0006), decide whether the shape is chartable and, if so,
// which chart to draw. The React layer only renders what this returns.

/** Rows small enough to read as bars/points; a single row is a scalar, a huge result is noise. */
const MIN_ROWS = 2;
const MAX_ROWS = 50;

export type ChartSpec = {
  kind: "bar" | "line";
  /** The category / x-axis column name. */
  labelKey: string;
  /** Numeric column names, one Recharts series each. */
  series: string[];
  /** Row objects keyed by column name: label as string, series values as numbers. */
  data: Array<Record<string, string | number>>;
};

/**
 * Parse a cell to a finite number, tolerating thousands separators and surrounding whitespace.
 * Returns `null` when the cell is not a plain number (so it counts as a label, not a series).
 */
export function parseNumeric(value: string): number | null {
  const trimmed = value.trim();
  if (trimmed === "") return null;
  // Strip thousands separators (commas) but keep the decimal point and a leading sign.
  const normalized = trimmed.replace(/,/g, "");
  if (!/^[+-]?(\d+(\.\d+)?|\.\d+)$/.test(normalized)) return null;
  const n = Number(normalized);
  return Number.isFinite(n) ? n : null;
}

// Group thousands for readable measures. The "es" locale only groups 5+ digit numbers (its
// minimumGroupingDigits is 2), so 4-digit years like "2024" stay ungrouped — exactly what we want.
const CELL_NUMBER_FORMAT = new Intl.NumberFormat("es", { maximumFractionDigits: 2 });

/**
 * Format a result cell for display: numbers get thousands separators (e.g. ``8000000.00`` →
 * ``8.000.000``); anything non-numeric is returned unchanged.
 */
export function formatCellValue(raw: string): string {
  const n = parseNumeric(raw);
  return n === null ? raw : CELL_NUMBER_FORMAT.format(n);
}

/** Whether every value in a column parses as a number. */
function isNumericColumn(rows: string[][], colIndex: number): boolean {
  return rows.every((row) => parseNumeric(row[colIndex] ?? "") !== null);
}

/**
 * Whether every value in the label column looks temporal: an ISO date, a `YYYY-MM` month, a bare
 * 4-digit year, or otherwise `Date.parse`-able. Used to pick line (time series) over bar.
 */
function isTemporalColumn(values: string[]): boolean {
  const looksTemporal = (raw: string): boolean => {
    const v = raw.trim();
    if (/^\d{4}-\d{2}$/.test(v)) return true; // YYYY-MM
    if (/^\d{4}-\d{2}-\d{2}([ T].*)?$/.test(v)) return true; // ISO date / datetime
    // Fall back to Date.parse but require a date separator, so a bare integer never reads as a date.
    // (A label column is non-numeric by construction — see analyzeResult — so a bare 4-digit year is a
    // numeric column, treated as a series, not a temporal axis. That "ingresos por año" shape is a known
    // limitation: we don't guess which of several numeric columns is the axis.)
    if (!/[-/:]/.test(v)) return false;
    return !Number.isNaN(Date.parse(v));
  };
  return values.every(looksTemporal);
}

/** Separator joining several label columns into one composite category (e.g. "origin · destination"). */
const LABEL_SEP = " · ";

/**
 * Decide whether a result is chartable and how. Returns `null` when it is not: requires at least one
 * non-numeric (label) column, at least one numeric column, and 2..50 rows.
 *
 * One label column is the x-axis directly. Several label columns are joined into one composite category
 * (e.g. `origin · destination` → "Ciudad del Este · Asuncion") — a "por ruta" result has two dimensions,
 * and this plots it as one bar per route. Numeric columns each become a series. A composite axis is never
 * temporal, so it is always a bar; a lone temporal label column draws a line.
 */
export function analyzeResult(columns: string[], rows: string[][]): ChartSpec | null {
  if (columns.length < 2) return null;
  if (rows.length < MIN_ROWS || rows.length > MAX_ROWS) return null;

  const numericCols: string[] = [];
  const labelCols: string[] = [];
  columns.forEach((name, i) => {
    if (isNumericColumn(rows, i)) numericCols.push(name);
    else labelCols.push(name);
  });

  // Need a category axis and something numeric to plot against it.
  if (labelCols.length === 0 || numericCols.length === 0) return null;

  const labelKey = labelCols.join(LABEL_SEP);
  const labelIndices = labelCols.map((name) => columns.indexOf(name));

  const data = rows.map((row) => {
    const label = labelIndices.map((i) => row[i] ?? "").join(LABEL_SEP);
    const obj: Record<string, string | number> = { [labelKey]: label };
    for (const name of numericCols) {
      const idx = columns.indexOf(name);
      obj[name] = parseNumeric(row[idx] ?? "") ?? 0;
    }
    return obj;
  });

  // Line only for a single, temporal label column; a composite axis is categorical → bar.
  const single = labelCols.length === 1;
  const labelValues = single ? rows.map((row) => row[labelIndices[0]] ?? "") : [];

  return {
    kind: single && isTemporalColumn(labelValues) ? "line" : "bar",
    labelKey,
    series: numericCols,
    data,
  };
}
