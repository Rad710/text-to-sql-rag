import type { FC } from "react";

import { cn } from "@/lib/utils";

import type { ConversationSummary } from "./history";

/** Sidebar: past conversations + "new chat" (task 0019). */
export const ConversationList: FC<{
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}> = ({ conversations, activeId, onSelect, onNew }) => (
  <aside className="border-border bg-muted/20 flex w-60 shrink-0 flex-col border-r">
    <div className="p-2">
      <button
        type="button"
        onClick={onNew}
        className="border-border/60 hover:bg-muted w-full rounded-lg border px-3 py-1.5 text-sm"
      >
        + Nueva conversación
      </button>
    </div>
    <nav className="flex-1 overflow-y-auto px-2 pb-2">
      {conversations.length === 0 ? (
        <p className="text-muted-foreground px-2 py-1.5 text-xs">Sin conversaciones todavía</p>
      ) : (
        conversations.map((c) => (
          <button
            type="button"
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={cn(
              "hover:bg-muted mb-0.5 block w-full truncate rounded-md px-2 py-1.5 text-start text-sm",
              c.id === activeId && "bg-muted font-medium",
            )}
            title={c.title}
          >
            {c.title}
          </button>
        ))
      )}
    </nav>
  </aside>
);
