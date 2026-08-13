import type {
    ChatModelAdapter,
    ThreadAssistantMessagePart,
    ThreadMessage,
} from "@assistant-ui/react";

import { apiFetch } from "@/api/client";
import i18n from "@/i18n";
import { type ToolStep, toolCallParts } from "@/lib/tool-parts";
import { useSession } from "@/stores/session";

/** Join a message's text parts (ignoring tool-call/other parts) into a plain string. */
function messageText(message: ThreadMessage): string {
    return message.content
        .map((part) => (part.type === "text" ? part.text : ""))
        .join(" ")
        .trim();
}

/**
 * The text of a prior turn for backend context. A live assistant turn carries a trailing **usage**
 * text part (steps · tokens · cost) on top of its answer part; that's UI chrome, not conversation, so
 * we drop it. Structural, not a regex: we only ever emit one answer part + one optional usage part, so
 * an assistant message with >1 text part has the usage footer last.
 */
function historyText(message: ThreadMessage): string {
    const texts = message.content.flatMap((part) => (part.type === "text" ? [part.text] : []));
    if (message.role === "assistant" && texts.length > 1) texts.pop();
    return texts.join(" ").trim();
}

// One Server-Sent Event from our FastAPI /chat stream.
type SSEEvent = { type: string; data: Record<string, unknown> };

/** Parse an SSE byte stream into typed events (event: <type>\ndata: <json>\n\n). */
async function* parseSSE(body: ReadableStream<Uint8Array>): AsyncGenerator<SSEEvent> {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        for (;;) {
            const sep = buffer.indexOf("\n\n");
            if (sep === -1) break;
            const frame = buffer.slice(0, sep);
            buffer = buffer.slice(sep + 2);
            let event = "message";
            let data = "";
            for (const line of frame.split("\n")) {
                if (line.startsWith("event:")) event = line.slice(6).trim();
                else if (line.startsWith("data:")) data += line.slice(5).trim();
            }
            if (data) yield { type: event, data: JSON.parse(data) as Record<string, unknown> };
        }
    }
}

/**
 * assistant-ui local runtime adapter: POST the question to /chat and translate our SSE events into
 * assistant-ui **message parts** so the agent's work renders natively — each `search_schema` /
 * `run_sql` call becomes a **tool-call part** (a collapsible step showing the SQL and its result),
 * followed by the answer and a token/cost usage part. Auth (and refresh-on-401) is handled by
 * `apiFetch`; conversation + feedback ids flow through the `useSession` store.
 */
export const adapter: ChatModelAdapter = {
    async *run({ messages, abortSignal }) {
        const question = messageText(messages[messages.length - 1]);
        // Prior turns (text only) give the backend conversational context (task 0016).
        const history = messages
            .slice(0, -1)
            .filter((m) => m.role === "user" || m.role === "assistant")
            .map((m) => ({ role: m.role, content: historyText(m) }))
            .filter((turn) => turn.content);

        const res = await apiFetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question,
                history,
                conversation_id: useSession.getState().conversationId,
                language: i18n.resolvedLanguage ?? "en", // drives the answer language (task 0040)
            }),
            signal: abortSignal,
        });

        if (!res.ok || !res.body) {
            // apiFetch already tried to refresh and signed out on a hard 401 → the session expired.
            if (res.status === 401) {
                yield { content: [{ type: "text", text: i18n.t("chat.sessionExpired") }] };
                return;
            }
            // Rate limited (decision 0010): the message is fully localized on the client now. A short
            // Retry-After (the per-minute limit) shows seconds; the long daily-cap wait says "later".
            if (res.status === 429) {
                const retry = Number(res.headers.get("Retry-After"));
                const short = retry > 0 && retry <= 90;
                const reason = i18n.t(short ? "chat.rateLimitMinute" : "chat.rateLimitDay");
                const hint = short
                    ? i18n.t("chat.retrySeconds", { seconds: retry })
                    : i18n.t("chat.retryLater");
                yield { content: [{ type: "text", text: `⚠️ ${reason}${hint}` }] };
                return;
            }
            yield {
                content: [
                    {
                        type: "text",
                        text: i18n.t("chat.error", {
                            status: res.status,
                            statusText: res.statusText,
                        }),
                    },
                ],
            };
            return;
        }

        // Tool steps are accumulated as events arrive (same shape we persist, task 0041); `pending`
        // points at the call awaiting its result. `toolCallParts` renders them — one shared mapping
        // with the reload path so a live turn and a reloaded one look identical.
        const steps: ToolStep[] = [];
        let pending = -1;
        let answer = "";
        let usage = "";

        for await (const evt of parseSSE(res.body)) {
            if (evt.type === "tool_start") {
                steps.push({
                    name: String(evt.data.name ?? "tool"),
                    arguments: (evt.data.arguments as Record<string, unknown> | undefined) ?? {},
                });
                pending = steps.length - 1;
            } else if (evt.type === "tool_result") {
                const idx = pending >= 0 ? pending : steps.length - 1;
                if (steps[idx]) {
                    const d = evt.data;
                    // run_sql carries structured rows (decision 0006) → rendered as a table; other tools
                    // carry a short text preview. Kept backend-native; `toolCallParts` normalizes it.
                    steps[idx].result = Array.isArray(d.rows)
                        ? {
                              columns: d.columns,
                              rows: d.rows,
                              row_count: d.row_count,
                              truncated: d.truncated,
                          }
                        : d.preview;
                }
                pending = -1;
            } else if (evt.type === "answer") {
                answer = String(evt.data.text ?? "");
            } else if (evt.type === "usage") {
                const d = evt.data;
                const cost = Number(d.cost_usd ?? 0).toFixed(4);
                usage = `\`${d.iterations} steps · ${d.total_tokens} tokens · $${cost}\``;
            } else if (evt.type === "conversation") {
                useSession.getState().setConversationId(String(evt.data.id)); // task 0019
                continue;
            } else if (evt.type === "message") {
                useSession.getState().setLastAssistantMessageId(String(evt.data.id)); // task 0020
                continue;
            } else {
                continue; // e.g. "done"
            }

            // Answer and usage are separate parts (no concatenation) — historyText drops the usage one.
            const content: ThreadAssistantMessagePart[] = [...toolCallParts(steps)];
            if (answer) content.push({ type: "text", text: answer });
            if (usage) content.push({ type: "text", text: usage });
            yield { content };
        }
    },
};
