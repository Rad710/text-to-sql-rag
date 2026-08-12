// Client for the conversation-history endpoints (task 0019), authenticated with the JWT.

import { getToken } from "./auth";

export type ConversationSummary = { id: string; title: string };
export type HistoryMessage = { id: string; role: "user" | "assistant"; content: string };

function authGet(path: string): Promise<Response> {
    return fetch(path, { headers: { Authorization: `Bearer ${getToken() ?? ""}` } });
}

export async function listConversations(): Promise<ConversationSummary[]> {
    const res = await authGet("/conversations");
    if (!res.ok) return [];
    return (await res.json()) as ConversationSummary[];
}

export async function getConversationMessages(id: string): Promise<HistoryMessage[]> {
    const res = await authGet(`/conversations/${id}`);
    if (!res.ok) return [];
    return ((await res.json()) as { messages: HistoryMessage[] }).messages;
}
