import { expect, test } from "vitest";

import { analyzeResult, formatCellValue, parseNumeric } from "./chart-data";

test("formatCellValue: groups measures, leaves years/text/small ints alone", () => {
  expect(formatCellValue("8000000.00")).toBe("8.000.000"); // money → grouped
  expect(formatCellValue("165500")).toBe("165.500");
  expect(formatCellValue("12.5")).toBe("12,5"); // es decimal comma
  expect(formatCellValue("2024")).toBe("2024"); // 4-digit year: not grouped
  expect(formatCellValue("4")).toBe("4");
  expect(formatCellValue("Asunción")).toBe("Asunción"); // non-numeric unchanged
  expect(formatCellValue("")).toBe("");
});

test("parseNumeric: plain, signed, decimal, and thousands-separated numbers", () => {
  expect(parseNumeric("8000000")).toBe(8000000);
  expect(parseNumeric("  8,000,000 ")).toBe(8000000);
  expect(parseNumeric("-12.5")).toBe(-12.5);
  expect(parseNumeric(".5")).toBe(0.5);
});

test("parseNumeric: non-numbers reject", () => {
  expect(parseNumeric("Asunción")).toBeNull();
  expect(parseNumeric("")).toBeNull();
  expect(parseNumeric("2024-01")).toBeNull();
  expect(parseNumeric("12ab")).toBeNull();
});

test("bar: one label column + one numeric column", () => {
  const spec = analyzeResult(
    ["ruta", "ingresos"],
    [
      ["Asunción", "8000000"],
      ["Encarnación", "5200000"],
      ["Ciudad del Este", "6100000"],
    ],
  );
  expect(spec).not.toBeNull();
  expect(spec?.kind).toBe("bar");
  expect(spec?.labelKey).toBe("ruta");
  expect(spec?.series).toEqual(["ingresos"]);
  expect(spec?.data[0]).toEqual({ ruta: "Asunción", ingresos: 8000000 });
});

test("line: temporal label column (YYYY-MM) → line, thousands parsed", () => {
  const spec = analyzeResult(
    ["mes", "ingresos"],
    [
      ["2024-01", "8,000,000"],
      ["2024-02", "9,100,000"],
      ["2024-03", "7,500,000"],
    ],
  );
  expect(spec?.kind).toBe("line");
  expect(spec?.data[1]).toEqual({ mes: "2024-02", ingresos: 9100000 });
});

test("line: ISO date label column is temporal", () => {
  expect(
    analyzeResult(
      ["fecha", "n"],
      [
        ["2024-01-15", "3"],
        ["2024-02-20", "5"],
      ],
    )?.kind,
  ).toBe("line");
});

test("reject: a bare-year axis is numeric, so it's not detected (known limitation)", () => {
  // "anio" parses as a number → both columns numeric → no single label axis → null.
  expect(
    analyzeResult(
      ["anio", "n"],
      [
        ["2022", "3"],
        ["2023", "5"],
      ],
    ),
  ).toBeNull();
});

test("multi-series: two numeric columns become two series", () => {
  const spec = analyzeResult(
    ["ruta", "ingresos", "viajes"],
    [
      ["Asunción", "8000000", "12"],
      ["Encarnación", "5200000", "9"],
    ],
  );
  expect(spec?.series).toEqual(["ingresos", "viajes"]);
  expect(spec?.data[0]).toEqual({ ruta: "Asunción", ingresos: 8000000, viajes: 12 });
});

test("reject: single row is a scalar, not a chart", () => {
  expect(analyzeResult(["total"], [["8000000"]])).toBeNull();
  expect(analyzeResult(["ruta", "ingresos"], [["Asunción", "8000000"]])).toBeNull();
});

test("reject: all-text result (no numeric column)", () => {
  expect(
    analyzeResult(
      ["ruta", "chofer"],
      [
        ["Asunción", "Juan"],
        ["Encarnación", "Ana"],
      ],
    ),
  ).toBeNull();
});

test("reject: no label column (every column numeric)", () => {
  expect(
    analyzeResult(
      ["a", "b"],
      [
        ["1", "2"],
        ["3", "4"],
      ],
    ),
  ).toBeNull();
});

test("composite axis: several label columns join into one bar category", () => {
  // The mock's "facturación por ruta" shape: origin + destination + revenue.
  const spec = analyzeResult(
    ["origin", "destination", "revenue"],
    [
      ["Ciudad del Este", "Asuncion", "8000000.00"],
      ["Asuncion", "Ciudad del Este", "6000000.00"],
    ],
  );
  expect(spec?.kind).toBe("bar");
  expect(spec?.labelKey).toBe("origin · destination");
  expect(spec?.series).toEqual(["revenue"]);
  expect(spec?.data[0]).toEqual({
    "origin · destination": "Ciudad del Este · Asuncion",
    revenue: 8000000,
  });
});

test("reject: more than 50 rows is noise", () => {
  const rows = Array.from({ length: 51 }, (_, i) => [`r${i}`, String(i + 1)]);
  expect(analyzeResult(["ruta", "n"], rows)).toBeNull();
});

test("reject: a single column can never be a chart", () => {
  expect(analyzeResult(["ingresos"], [["8000000"], ["5200000"]])).toBeNull();
});
