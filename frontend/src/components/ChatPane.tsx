import {
    AssistantRuntimeProvider,
    type ThreadMessageLike,
    useLocalRuntime,
} from "@assistant-ui/react";
import type { FC } from "react";

import { getLastAssistantMessageId, submitFeedback } from "@/api/feedback";
import { Thread } from "@/components/assistant-ui/thread";
import { OpenToolGroup, ToolRenderer } from "@/components/RunSqlTool";
import { Welcome } from "@/components/Welcome";
import { adapter } from "@/lib/runtime";

/**
 * A fresh local runtime seeded with a conversation's prior messages. Remounted (via `key`) when the
 * active conversation changes, so switching threads re-seeds the runtime (task 0019).
 */
export const ChatPane: FC<{ initialMessages: ThreadMessageLike[] }> = ({ initialMessages }) => {
    const runtime = useLocalRuntime(adapter, {
        initialMessages,
        adapters: {
            // Thumbs on the latest answer (the action bar autohides on older ones) → POST /feedback (0020).
            feedback: {
                submit: ({ type }) => {
                    const id = getLastAssistantMessageId();
                    if (id) void submitFeedback(id, type === "positive" ? 1 : -1);
                },
            },
        },
    });
    return (
        <AssistantRuntimeProvider runtime={runtime}>
            <Thread
                components={{ Welcome, ToolFallback: ToolRenderer, ToolGroup: OpenToolGroup }}
            />
        </AssistantRuntimeProvider>
    );
};
