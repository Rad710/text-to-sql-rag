// Client for the conversation-history endpoints (task 0019). apiFetch carries the access token.

import { apiFetch } from "@/api/client";

export type ConversationSummary = { id: string; title: string };
export type HistoryMessage = { id: string; role: "user" | "assistant"; content: string };

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
