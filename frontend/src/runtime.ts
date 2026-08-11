import type {
  ChatModelAdapter,
  ThreadAssistantMessagePart,
  ThreadMessage,
  ToolCallMessagePart,
} from "@assistant-ui/react";

import { getToken } from "./auth";
import { getConversationId, notifyConversation } from "./conversation";
import { setLastAssistantMessageId } from "./feedback";

/** Join a message's text parts (ignoring tool-call/other parts) into a plain string. */
function messageText(message: ThreadMessage): string {
  return message.content
    .map((part) => (part.type === "text" ? part.text : ""))
    .join(" ")
    .trim();
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
 * assistant-ui local runtime adapter: POST the question to /chat and translate our SSE events
 * into assistant-ui **message parts** so the agent's work renders natively — each `search_schema`
 * / `run_sql` call becomes a **tool-call part** (a collapsible step showing the SQL and its result),
 * followed by the answer and a token/cost footer. This is the tool-call rendering
 * [decision 0005](../../docs/decisions/0005-custom-fastapi-sse-react-frontend.md) called for; the
 * styled Thread's `ToolFallback`/`ToolGroup` render the parts.
 */
export const adapter: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    const question = messageText(messages[messages.length - 1]);
    // Prior turns (text only) so the backend can give the model conversational context (task 0016).
    const history = messages
      .slice(0, -1)
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({
        role: m.role,
        // Drop the UI-only token/cost footer from assistant turns — it's chrome, not conversation.
        content: messageText(m)
          .replace(/\n*`[^`\n]*·[^`\n]*`\s*$/, "")
          .trim(),
      }))
      .filter((turn) => turn.content);

    const token = getToken();
    const res = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ question, history, conversation_id: getConversationId() }),
      signal: abortSignal,
    });
    if (!res.ok || !res.body) {
      yield { content: [{ type: "text", text: `⚠️ ${res.status} ${res.statusText}` }] };
      return;
    }

    // Tool-call parts are built as events arrive; `pending` points at the call awaiting its result.
    const tools: ToolCallMessagePart[] = [];
    let pending = -1;
    let answer = "";
    let usage = "";

    for await (const evt of parseSSE(res.body)) {
      if (evt.type === "tool_start") {
        const name = String(evt.data.name ?? "tool");
        const args = (evt.data.arguments as Record<string, unknown> | undefined) ?? {};
        tools.push({
          type: "tool-call",
          toolCallId: `${name}-${tools.length}`,
          toolName: name,
          args: args as ToolCallMessagePart["args"],
          // Show the meaningful argument as plain text in the collapsible step — the SQL for
          // run_sql, the question for search_schema — instead of raw JSON.
          argsText: String(args.query ?? args.question ?? JSON.stringify(args)),
        });
        pending = tools.length - 1;
      } else if (evt.type === "tool_result") {
        const idx = pending >= 0 ? pending : tools.length - 1;
        if (tools[idx]) {
          const d = evt.data;
          // run_sql carries structured rows (decision 0006) → the frontend renders the table;
          // other tools carry a short text preview.
          const result = Array.isArray(d.rows)
            ? { columns: d.columns, rows: d.rows, rowCount: d.row_count, truncated: d.truncated }
            : d.preview;
          tools[idx] = { ...tools[idx], result };
        }
        pending = -1;
      } else if (evt.type === "answer") {
        answer = String(evt.data.text ?? "");
      } else if (evt.type === "usage") {
        const d = evt.data;
        const cost = Number(d.cost_usd ?? 0).toFixed(4);
        usage = `\`${d.iterations} steps · ${d.total_tokens} tokens · $${cost}\``;
      } else if (evt.type === "conversation") {
        notifyConversation(String(evt.data.id)); // task 0019 — remember which conversation this is
        continue;
      } else if (evt.type === "message") {
        setLastAssistantMessageId(String(evt.data.id)); // task 0020 — feedback targets this message
        continue;
      } else {
        continue; // e.g. "done"
      }

      const content: ThreadAssistantMessagePart[] = [...tools];
      const trailing = [answer, usage].filter(Boolean).join("\n\n");
      if (trailing) content.push({ type: "text", text: trailing });
      yield { content };
    }
  },
};
