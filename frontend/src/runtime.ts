import type { ChatModelAdapter } from "@assistant-ui/react";

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
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
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
 * (tool_start / run_sql / answer / usage) into a progressively-built markdown message — the SQL
 * as a code block, then the answer, then a token/cost footer.
 */
export const adapter: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    const last = messages[messages.length - 1];
    const question = last.content
      .map((part) => (part.type === "text" ? part.text : ""))
      .join(" ")
      .trim();

    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
      signal: abortSignal,
    });
    if (!res.ok || !res.body) {
      yield { content: [{ type: "text", text: `⚠️ ${res.status} ${res.statusText}` }] };
      return;
    }

    let markdown = "";
    for await (const evt of parseSSE(res.body)) {
      if (evt.type === "tool_start") {
        const args = evt.data.arguments as Record<string, unknown> | undefined;
        if (evt.data.name === "run_sql" && args?.query) {
          markdown += "```sql\n" + String(args.query) + "\n```\n\n";
        } else {
          continue;
        }
      } else if (evt.type === "answer") {
        markdown += String(evt.data.text ?? "");
      } else if (evt.type === "usage") {
        const d = evt.data;
        const cost = Number(d.cost_usd ?? 0).toFixed(4);
        markdown += `\n\n\`${d.iterations} steps · ${d.total_tokens} tokens · $${cost}\``;
      } else {
        continue;
      }
      yield { content: [{ type: "text", text: markdown }] };
    }
  },
};
