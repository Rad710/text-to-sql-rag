// Feedback client (task 0020). The action bar (autohide="not-last") only shows on the latest answer,
// so feedback always targets the most-recent assistant message id — tracked in the session store
// (set from the /chat `message` event, or the last message of a reloaded conversation).

import { apiFetch } from "@/api/client";

export async function submitFeedback(messageId: string, rating: 1 | -1): Promise<void> {
    await apiFetch("/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: messageId, rating }),
    });
}
