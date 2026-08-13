import { expect, test } from "vitest";

import { isSqlResult } from "@/components/ResultView";
import { type ToolStep, toolCallParts } from "@/lib/tool-parts";

// The shared mapping both the live stream and a reloaded conversation use to build the SQL step +
// result table (task 0041) — so a reloaded turn renders identically to the live one.

test("run_sql step exposes the SQL as argsText and a table-shaped result", () => {
    const steps: ToolStep[] = [
        {
            name: "run_sql",
            arguments: { query: "SELECT route, total FROM billing" },
            // Backend-native (snake_case) result, exactly as persisted / streamed.
            result: {
                columns: ["route", "total"],
                rows: [["Encarnación", "100"]],
                row_count: 1,
                truncated: false,
            },
        },
    ];
    const [part] = toolCallParts(steps);
    expect(part.type).toBe("tool-call");
    expect(part.toolName).toBe("run_sql");
    expect(part.argsText).toBe("SELECT route, total FROM billing");
    // Normalized to the camelCase shape ResultView reads → renders as a table, not raw JSON.
    expect(isSqlResult(part.result)).toBe(true);
    expect((part.result as { rowCount: number }).rowCount).toBe(1);
});

test("search_schema step keeps its text preview and derives argsText from the question", () => {
    const [part] = toolCallParts([
        { name: "search_schema", arguments: { question: "rutas" }, result: "route(code, price)" },
    ]);
    expect(part.argsText).toBe("rutas");
    expect(part.result).toBe("route(code, price)");
    expect(isSqlResult(part.result)).toBe(false);
});

test("a step still awaiting its result carries no result key (renders as pending)", () => {
    const [part] = toolCallParts([{ name: "run_sql", arguments: { query: "SELECT 1" } }]);
    expect(part.result).toBeUndefined();
});
