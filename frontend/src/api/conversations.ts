// Client for the conversation-history endpoints (task 0019). apiFetch carries the access token.

import { apiFetch } from "@/api/client";
import type { ToolStep } from "@/lib/tool-parts";

export type ConversationSummary = { id: string; title: string };
export type HistoryMessage = {
    id: string;
    role: "user" | "assistant";
    content: string;
    // The assistant turn's tool steps (task 0041); absent/null on user turns and pre-0041 messages.
    tool_data?: ToolStep[] | null;
};

export async function listConversations(): Promise<ConversationSummary[]> {
    const res = await apiFetch("/conversations");
    if (!res.ok) return [];
    return (await res.json()) as ConversationSummary[];
}

export async function getConversationMessages(id: string): Promise<HistoryMessage[]> {
    const res = await apiFetch(`/conversations/${id}`);
    if (!res.ok) return [];
    return ((await res.json()) as { messages: HistoryMessage[] }).messages;
}
