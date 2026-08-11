import type { ThreadMessage } from "@assistant-ui/react";
import { afterEach, expect, test, vi } from "vitest";

import { adapter } from "./runtime";

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

function userMessage(text: string): ThreadMessage {
  return { role: "user", content: [{ type: "text", text }] } as unknown as ThreadMessage;
}

/** Drain the adapter's async generator and return the last yielded chunk's joined text. */
type Chunk = { content?: Array<{ type: string; text?: string }> };

async function runToText(): Promise<string> {
  const gen = adapter.run({
    messages: [userMessage("¿cuánto facturamos?")],
    abortSignal: new AbortController().signal,
  } as unknown as Parameters<typeof adapter.run>[0]) as AsyncGenerator<Chunk>;
  let last = "";
  for await (const chunk of gen) {
    last = (chunk.content ?? [])
      .map((p) => (p.type === "text" ? p.text : ""))
      .join("")
      .trim();
  }
  return last;
}

function rateLimited(retryAfter: string, detail: string): typeof fetch {
  return vi.fn(async () => ({
    ok: false,
    status: 429,
    statusText: "Too Many Requests",
    body: null,
    headers: new Headers({ "Retry-After": retryAfter }),
    json: async () => ({ detail }),
  })) as unknown as typeof fetch;
}

// A 429 from /chat (rate limit, decision 0010) surfaces the backend's reason + our retry hint — not a
// raw "429 Too Many Requests". Short per-minute waits show seconds.
test("renders seconds hint for a short per-minute rate limit (429)", async () => {
  vi.stubGlobal("fetch", rateLimited("30", "Demasiadas consultas seguidas."));
  const text = await runToText();
  expect(text).toMatch(/demasiadas consultas seguidas/i);
  expect(text).toMatch(/en 30 s/);
  expect(text).not.toMatch(/más tarde/);
});

// The daily cap returns a long Retry-After (seconds to midnight) — we collapse that to "más tarde"
// instead of dumping tens of thousands of seconds at the user.
test("renders 'más tarde' for the long daily-cap wait (429)", async () => {
  vi.stubGlobal("fetch", rateLimited("28302", "Alcanzaste el límite diario de consultas."));
  const text = await runToText();
  expect(text).toMatch(/límite diario de consultas/i);
  expect(text).toMatch(/más tarde/);
  expect(text).not.toMatch(/\d+ s/);
});
