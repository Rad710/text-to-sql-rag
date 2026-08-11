import type { ComponentType, PropsWithChildren } from "react";

import type { ToolCallMessagePartComponent } from "@assistant-ui/react";

import { ToolFallback } from "@/components/assistant-ui/tool-fallback";
import {
  ToolGroupContent,
  ToolGroupRoot,
  ToolGroupTrigger,
} from "@/components/assistant-ui/tool-group";
import type { ThreadGroupPart } from "@/components/assistant-ui/thread";

/** Structured result carried on the `run_sql` tool-call part (decision 0006). */
type SqlResult = {
  columns: string[];
  rows: string[][];
  rowCount: number;
  truncated: boolean;
};

function isSqlResult(value: unknown): value is SqlResult {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return Array.isArray(v.columns) && Array.isArray(v.rows);
}

/** The query result rendered as a real table from structured rows — the payoff of decision 0005/0006. */
function ResultTable({ columns, rows, rowCount, truncated }: SqlResult) {
  return (
    <div className="aui-sql-result overflow-x-auto">
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
            <tr key={r}>
              {row.map((cell, c) => (
                <td
                  key={c}
                  className="border-muted-foreground/20 border-b border-s px-3 py-1.5 last:border-e"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-muted-foreground mt-1 text-xs">
        {rowCount} {rowCount === 1 ? "row" : "rows"}
        {truncated ? ", truncated" : ""}
      </p>
    </div>
  );
}

/**
 * Tool-call renderer: `run_sql` shows the generated SQL plus the result **table** (open by default,
 * since it's the answer's evidence); every other tool falls back to the default collapsible step.
 */
export const ToolRenderer: ToolCallMessagePartComponent = (props) => {
  if (props.toolName === "run_sql" && isSqlResult(props.result)) {
    return (
      <ToolFallback.Root defaultOpen>
        <ToolFallback.Trigger toolName="run_sql" status={props.status} />
        <ToolFallback.Content>
          <ToolFallback.Args argsText={props.argsText} />
          <ResultTable {...props.result} />
        </ToolFallback.Content>
      </ToolFallback.Root>
    );
  }
  return <ToolFallback {...props} />;
};

/** Tool-call group, open by default so the SQL + result table are visible without a click. */
export const OpenToolGroup: ComponentType<PropsWithChildren<{ group: ThreadGroupPart }>> = ({
  group,
  children,
}) => (
  <ToolGroupRoot variant="ghost" defaultOpen>
    <ToolGroupTrigger count={group.indices.length} active={group.status.type === "running"} />
    <ToolGroupContent>{children}</ToolGroupContent>
  </ToolGroupRoot>
);
