import type { ThreadMessageLike } from "@assistant-ui/react";
import { Menu } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import {
    type ConversationSummary,
    getConversationMessages,
    listConversations,
} from "@/api/conversations";
import { setLastAssistantMessageId } from "@/api/feedback";
import { ChatPane } from "@/components/ChatPane";
import { ConversationSidebar } from "@/components/ConversationSidebar";
import { useAuth } from "@/hooks/useAuth";
import { useServerMode } from "@/hooks/useServerMode";
import { onConversationStarted, setConversationId } from "@/lib/active-conversation";

/** / — the authenticated chat app: header + conversation sidebar (drawer on mobile) + the chat pane. */
export function ChatPage() {
    const { user, logout } = useAuth();
    const modeLabel = useServerMode();

    const [conversations, setConversations] = useState<ConversationSummary[]>([]);
    const [activeId, setActiveId] = useState<string | null>(null);
    const [initialMessages, setInitialMessages] = useState<ThreadMessageLike[]>([]);
    const [paneKey, setPaneKey] = useState(0); // bumped only to remount ChatPane (switch/new)
    const [sidebarOpen, setSidebarOpen] = useState(false); // mobile drawer (task 0026)

    const refreshList = useCallback(async () => {
        setConversations(await listConversations());
    }, []);

    useEffect(() => {
        // Fresh session: start with no active conversation / feedback target until one is opened or started.
        setConversationId(null);
        setLastAssistantMessageId(null);
        void refreshList();
        // When a turn (re)identifies its conversation, highlight it + refresh the list — no remount.
        onConversationStarted((id) => {
            setActiveId(id);
            void refreshList();
        });
        return () => onConversationStarted(null);
    }, [refreshList]);

    const startNew = useCallback(() => {
        setConversationId(null);
        setLastAssistantMessageId(null);
        setInitialMessages([]);
        setActiveId(null);
        setPaneKey((k) => k + 1);
        setSidebarOpen(false);
    }, []);

    const openConversation = useCallback(async (id: string) => {
        const messages = await getConversationMessages(id);
        setConversationId(id);
        // The latest answer (the only one showing an action bar) is what feedback targets on reload.
        const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
        setLastAssistantMessageId(lastAssistant?.id ?? null);
        setInitialMessages(messages.map((m) => ({ role: m.role, content: m.content })));
        setActiveId(id);
        setPaneKey((k) => k + 1);
        setSidebarOpen(false);
    }, []);

    return (
        <div className="flex h-full flex-col">
            <header className="border-border flex items-center justify-between gap-3 border-b px-4 py-3.5 md:px-6">
                <div className="flex min-w-0 items-center gap-2 md:gap-3">
                    <button
                        type="button"
                        onClick={() => setSidebarOpen(true)}
                        aria-label="Abrir conversaciones"
                        className="text-muted-foreground hover:text-foreground -ml-1 shrink-0 md:hidden"
                    >
                        <Menu className="size-5" />
                    </button>
                    <span className="truncate font-semibold">
                        🚚 DYR Transportes — Data Assistant
                    </span>
                    <span className="text-muted-foreground hidden text-xs sm:inline">
                        text-to-SQL · RAG{modeLabel ? ` · ${modeLabel}` : ""}
                    </span>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                    <span className="text-muted-foreground hidden text-xs sm:inline">
                        {user?.name}
                    </span>
                    <button
                        type="button"
                        onClick={logout}
                        className="text-muted-foreground hover:text-foreground text-xs underline underline-offset-2"
                    >
                        Salir
                    </button>
                </div>
            </header>
            <div className="relative flex min-h-0 flex-1">
                <ConversationSidebar
                    conversations={conversations}
                    activeId={activeId}
                    onSelect={openConversation}
                    onNew={startNew}
                    open={sidebarOpen}
                    onClose={() => setSidebarOpen(false)}
                />
                <div className="min-h-0 flex-1">
                    <ChatPane key={paneKey} initialMessages={initialMessages} />
                </div>
            </div>
        </div>
    );
}
