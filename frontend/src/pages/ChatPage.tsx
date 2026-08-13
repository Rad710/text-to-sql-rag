import type { ThreadMessageLike } from "@assistant-ui/react";
import { Menu } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
    type ConversationSummary,
    getConversationMessages,
    listConversations,
} from "@/api/conversations";
import { ChatPane } from "@/components/ChatPane";
import { ConversationSidebar } from "@/components/ConversationSidebar";
import { LanguageToggle } from "@/components/LanguageToggle";
import { useAuth } from "@/hooks/useAuth";
import { useServerMode } from "@/hooks/useServerMode";
import { toolCallParts } from "@/lib/tool-parts";
import { useSession } from "@/stores/session";

/** / — the authenticated chat app: header + conversation sidebar (drawer on mobile) + the chat pane. */
export function ChatPage() {
    const { t } = useTranslation();
    const { user, logout } = useAuth();
    const modeLabel = useServerMode();

    const [conversations, setConversations] = useState<ConversationSummary[]>([]);
    const [activeId, setActiveId] = useState<string | null>(null);
    const [initialMessages, setInitialMessages] = useState<ThreadMessageLike[]>([]);
    const [paneKey, setPaneKey] = useState(0); // bumped only to remount ChatPane (switch/new)
    const [sidebarOpen, setSidebarOpen] = useState(false); // mobile drawer (task 0026)

    // When a turn (re)identifies its conversation (the runtime writes it to the store), highlight it
    // and refresh the list — no remount. Reactive via the store, not a hand-rolled callback registry.
    const conversationId = useSession((s) => s.conversationId);

    const refreshList = useCallback(async () => {
        setConversations(await listConversations());
    }, []);

    useEffect(() => {
        // Fresh session: no active conversation / feedback target until one is opened or started.
        useSession.getState().resetConversation();
        void refreshList();
    }, [refreshList]);

    useEffect(() => {
        if (conversationId) {
            setActiveId(conversationId);
            void refreshList();
        }
    }, [conversationId, refreshList]);

    const startNew = useCallback(() => {
        useSession.getState().resetConversation();
        setInitialMessages([]);
        setActiveId(null);
        setPaneKey((k) => k + 1);
        setSidebarOpen(false);
    }, []);

    const openConversation = useCallback(async (id: string) => {
        const messages = await getConversationMessages(id);
        const { setConversationId, setLastAssistantMessageId } = useSession.getState();
        setConversationId(id);
        // The latest answer (the only one showing an action bar) is what feedback targets on reload.
        const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
        setLastAssistantMessageId(lastAssistant?.id ?? null);
        // Rebuild the tool steps (SQL step + result table) that only streamed live before (task 0041);
        // the same `toolCallParts` the live runtime uses, so a reloaded turn renders identically. A
        // message without tool_data (user turns, pre-0041 rows) stays a plain string → prose-only.
        setInitialMessages(
            messages.map((m) =>
                m.tool_data?.length
                    ? {
                          role: m.role,
                          content: [
                              ...toolCallParts(m.tool_data),
                              ...(m.content ? [{ type: "text" as const, text: m.content }] : []),
                          ],
                      }
                    : { role: m.role, content: m.content },
            ),
        );
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
                        aria-label={t("common.openMenu")}
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
                    <LanguageToggle />
                    <button
                        type="button"
                        onClick={logout}
                        className="text-muted-foreground hover:text-foreground text-xs underline underline-offset-2"
                    >
                        {t("common.logout")}
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
