import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";

import App from "./App";

/** Build a fake /chat Response whose body streams the given SSE frames. */
function sseResponse(frames: string[]): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      for (const f of frames) controller.enqueue(encoder.encode(f));
      controller.close();
    },
  });
  return { ok: true, status: 200, statusText: "OK", body } as unknown as Response;
}

afterEach(() => {
  vi.restoreAllMocks();
});

// The regression that shipped "done" but crashed: assistant-ui's runtime threw on mount
// under React 19, and tsc/vite build never executed a mount. This test mounts <App />, so
// the runtime initialises exactly as in the browser — a mount-time throw fails here.
test("mounts without crashing and shows the shell", async () => {
  render(<App />);
  // Present immediately on mount (a mount-time runtime crash would throw before this).
  expect(
    screen.getByText(/DYR Transportes — Data Assistant/),
  ).toBeInTheDocument();
  // The empty-thread welcome + suggestions render after the runtime settles (effect).
  expect(
    await screen.findByRole("heading", { name: /qué querés saber/i }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: /facturación total por ruta/i }),
  ).toBeInTheDocument();
  expect(screen.getByRole("textbox", { name: /message input/i })).toBeInTheDocument();
});

// Full wiring in jsdom: a suggestion click POSTs to /chat, and the SSE tool events are mapped to
// assistant-ui tool-call parts (rendered as a collapsible step group — decision 0005), followed by
// the answer and the token/cost footer.
test("renders tool-call steps, the answer and the usage footer", async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    sseResponse([
      'event: tool_start\ndata: {"name": "search_schema", "arguments": {"question": "q"}}\n\n',
      'event: tool_result\ndata: {"name": "search_schema", "preview": "table shipment(...)"}\n\n',
      'event: tool_start\ndata: {"name": "run_sql", "arguments": {"query": "SELECT 1"}}\n\n',
      'event: tool_result\ndata: {"name": "run_sql", "preview": "n\\n42"}\n\n',
      'event: answer\ndata: {"text": "Según la base de datos: 1 fila."}\n\n',
      'event: usage\ndata: {"iterations": 3, "total_tokens": 3400, "cost_usd": 0}\n\n',
    ]),
  );
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);
  await userEvent.click(
    await screen.findByRole("button", { name: /facturación total por ruta/i }),
  );

  // Both tool_start events become tool-call parts → a collapsible "2 tool calls" step group.
  expect(await screen.findByText(/2 tool calls/i)).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/chat", expect.objectContaining({ method: "POST" }));
  expect(screen.getByText(/Según la base de datos/)).toBeInTheDocument();
  expect(screen.getByText(/3 steps · 3400 tokens · \$0\.0000/)).toBeInTheDocument();
});
