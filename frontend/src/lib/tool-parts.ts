import type { ToolCallMessagePart } from "@assistant-ui/react";

/**
 * One tool step of an assistant turn — the neutral shape both the **live** SSE stream (`runtime.ts`)
 * and a **reloaded** conversation (`ChatPage`) build parts from, so the two paths can't drift (task
 * 0041). `result` is a `run_sql` structured result (backend snake_case) or a short text preview.
 */
export type ToolStep = {
    name: string;
    arguments?: Record<string, unknown>;
    result?: unknown;
};

/** A `run_sql` structured result in the camelCase shape `ResultView` reads; other results pass through. */
function normalizeResult(result: unknown): unknown {
    if (
        result &&
        typeof result === "object" &&
        Array.isArray((result as { rows?: unknown }).rows)
    ) {
        const d = result as Record<string, unknown>;
        return {
            columns: d.columns,
            rows: d.rows,
            rowCount: d.rowCount ?? d.row_count,
            truncated: d.truncated,
        };
    }
    return result;
}

/** Build assistant-ui tool-call parts from tool steps. The single source for the SQL step + table. */
export function toolCallParts(steps: ToolStep[]): ToolCallMessagePart[] {
    return steps.map((step, i) => {
        const args = step.arguments ?? {};
        return {
            type: "tool-call",
            toolCallId: `${step.name}-${i}`,
            toolName: step.name,
            args: args as ToolCallMessagePart["args"],
            // The meaningful argument as plain text in the collapsible step — the SQL for run_sql
            // (models name it `query` or, for some local ones, `sql`), the question for search_schema.
            argsText: String(args.query ?? args.sql ?? args.question ?? JSON.stringify(args)),
            ...(step.result !== undefined ? { result: normalizeResult(step.result) } : {}),
        };
    });
}
