import type { FC } from "react";

import { cn } from "@/lib/utils";

import type { ConversationSummary } from "./history";

/**
 * Sidebar: past conversations + "new chat" (task 0019). Responsive (task 0026): on `md+` it's a static
 * left column; on mobile it's an overlay drawer that slides in from the left over a dimmed backdrop.
 */
export const ConversationList: FC<{
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  open: boolean;
  onClose: () => void;
}> = ({ conversations, activeId, onSelect, onNew, open, onClose }) => (
  <>
    {/* Mobile backdrop — dims the content and closes the drawer on tap. Hidden on md+. */}
    {open && (
      <button
        type="button"
        aria-label="Cerrar menú"
        onClick={onClose}
        className="fixed inset-0 z-30 bg-black/40 md:hidden"
      />
    )}
    <aside
      className={cn(
        // Mobile: fixed overlay drawer, off-canvas until opened.
        "fixed inset-y-0 left-0 z-40 flex w-72 max-w-[80%] transform flex-col shadow-lg transition-transform duration-200",
        open ? "translate-x-0" : "-translate-x-full",
        // Desktop: a static, always-visible column.
        "md:static md:z-auto md:w-60 md:max-w-none md:translate-x-0 md:shadow-none",
        // Solid background on mobile (it overlays content); subtle tint on desktop.
        "border-border bg-background md:bg-muted/20 shrink-0 border-r",
      )}
    >
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
  </>
);
