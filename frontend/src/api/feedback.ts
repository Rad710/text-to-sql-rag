// Feedback client (task 0020). The action bar (autohide="not-last") only shows on the latest answer,
// so feedback always targets the most-recent assistant message id — set from the /chat `message` event
// or from the last message of a reloaded conversation.

import { getToken } from "./auth";

let lastAssistantMessageId: string | null = null;

export function setLastAssistantMessageId(id: string | null): void {
    lastAssistantMessageId = id;
}

export function getLastAssistantMessageId(): string | null {
    return lastAssistantMessageId;
}

export async function submitFeedback(messageId: string, rating: 1 | -1): Promise<void> {
    await fetch("/feedback", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getToken() ?? ""}`,
        },
        body: JSON.stringify({ message_id: messageId, rating }),
    });
}
