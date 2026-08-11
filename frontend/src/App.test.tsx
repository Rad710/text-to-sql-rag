import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";

import App from "./App";

/** Fake /chat Response whose body streams the given SSE frames. */
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

/** Fake JSON Response (for /auth/me). */
function jsonResponse(data: unknown): Response {
  return { ok: true, status: 200, json: async () => data } as unknown as Response;
}

const SSE_FRAMES = [
  'event: conversation\ndata: {"id": "conv-1"}\n\n',
  'event: tool_start\ndata: {"name": "search_schema", "arguments": {"question": "q"}}\n\n',
  'event: tool_result\ndata: {"name": "search_schema", "preview": "table shipment(...)"}\n\n',
  'event: tool_start\ndata: {"name": "run_sql", "arguments": {"query": "SELECT 1"}}\n\n',
  'event: tool_result\ndata: {"name": "run_sql", "columns": ["revenue"], "rows": [["8000000"]], "row_count": 1, "truncated": false}\n\n',
  'event: answer\ndata: {"text": "Consulté la base de datos para responder."}\n\n',
  'event: usage\ndata: {"iterations": 3, "total_tokens": 3400, "cost_usd": 0}\n\n',
];

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

// Mount-crash guard (assistant-ui's runtime threw on mount under React 19, which tsc/build missed).
// Unauthenticated, App resolves the auth check to "no user" and shows the login screen.
test("mounts without crashing and shows the login screen when unauthenticated", async () => {
  render(<App />);
  expect(await screen.findByRole("heading", { name: /DYR Transportes/i })).toBeInTheDocument();
  expect(screen.getByLabelText("Email")).toBeInTheDocument();
  expect(screen.getByLabelText("Contraseña")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /entrar/i })).toBeInTheDocument();
});

// Authenticated (token in storage + /auth/me → a user): the chat renders. A suggestion click POSTs to
// /chat with the Bearer token; SSE tool events map to a collapsible step group (0005), run_sql's rows
// render as a real table (0006), and the answer + usage follow.
test("authenticated: renders tool steps + result table + answer, and sends the Bearer token", async () => {
  localStorage.setItem("dyr_token", "tok-abc");
  const fetchMock = vi.fn((input: RequestInfo | URL, _init?: RequestInit) => {
    const url = String(input);
    if (url === "/auth/me") {
      return Promise.resolve(jsonResponse({ id: "u1", email: "a@b.com", name: "Ana" }));
    }
    if (url === "/conversations") {
      return Promise.resolve(jsonResponse([]));
    }
    return Promise.resolve(sseResponse(SSE_FRAMES));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);
  await userEvent.click(await screen.findByRole("button", { name: /facturación total por ruta/i }));

  expect(await screen.findByText(/2 tool calls/i)).toBeInTheDocument();
  expect(screen.getByRole("table")).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "revenue" })).toBeInTheDocument();
  expect(screen.getByRole("cell", { name: "8000000" })).toBeInTheDocument();
  expect(screen.getByText(/Consulté la base de datos/)).toBeInTheDocument();
  expect(screen.getByText(/3 steps · 3400 tokens · \$0\.0000/)).toBeInTheDocument();

  const chatCall = fetchMock.mock.calls.find((c) => String(c[0]) === "/chat");
  expect(chatCall).toBeDefined();
  const init = chatCall?.[1] as RequestInit;
  expect((init.headers as Record<string, string>).Authorization).toBe("Bearer tok-abc");
  const body = JSON.parse(init.body as string);
  expect(body.question).toMatch(/facturación total por ruta/);
  expect(body.history).toEqual([]);
});
