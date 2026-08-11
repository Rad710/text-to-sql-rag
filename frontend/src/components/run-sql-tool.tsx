import type { ToolCallMessagePartComponent } from "@assistant-ui/react";
import type { ComponentType, PropsWithChildren } from "react";
import type { ThreadGroupPart } from "@/components/assistant-ui/thread";
import { ToolFallback } from "@/components/assistant-ui/tool-fallback";
import {
  ToolGroupContent,
  ToolGroupRoot,
  ToolGroupTrigger,
} from "@/components/assistant-ui/tool-group";
import { isSqlResult, ResultView } from "@/components/result-view";

/**
 * Tool-call renderer: `run_sql` shows the generated SQL plus the result **view** (a table, plus a
 * Tabla/Gráfico toggle when the shape fits — decisions 0005/0006/0021); open by default since it's the
 * answer's evidence. Every other tool falls back to the default collapsible step.
 */
export const ToolRenderer: ToolCallMessagePartComponent = (props) => {
  if (props.toolName === "run_sql" && isSqlResult(props.result)) {
    return (
      <ToolFallback.Root defaultOpen>
        <ToolFallback.Trigger toolName="run_sql" status={props.status} />
        <ToolFallback.Content>
          <ToolFallback.Args argsText={props.argsText} />
          <ResultView {...props.result} />
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
