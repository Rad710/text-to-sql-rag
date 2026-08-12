import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";

import App from "@/App";

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
    'event: tool_result\ndata: {"name": "run_sql", "columns": ["ruta", "ingresos"], "rows": [["Asunción", "8000000"], ["Encarnación", "5200000"]], "row_count": 2, "truncated": false}\n\n',
    'event: answer\ndata: {"text": "Consulté la base de datos para responder."}\n\n',
    'event: usage\ndata: {"iterations": 3, "total_tokens": 3400, "cost_usd": 0}\n\n',
    'event: message\ndata: {"id": "msg-9"}\n\n',
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
        if (url === "/health") {
            return Promise.resolve(jsonResponse({ status: "ok", llm_mode: "mock", model: "mock" }));
        }
        if (url === "/conversations") {
            return Promise.resolve(jsonResponse([]));
        }
        if (url === "/feedback") {
            return Promise.resolve({ ok: true, status: 204 } as Response);
        }
        return Promise.resolve(sseResponse(SSE_FRAMES));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await userEvent.click(
        await screen.findByRole("button", { name: /facturación total por ruta/i }),
    );

    expect(await screen.findByText(/2 tool calls/i)).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "ruta" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "ingresos" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "Asunción" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "8.000.000" })).toBeInTheDocument(); // grouped (task 0028)
    expect(screen.getByText(/Consulté la base de datos/)).toBeInTheDocument();
    expect(screen.getByText(/3 steps · 3400 tokens · \$0\.0000/)).toBeInTheDocument();

    // The result is chartable (label + numeric, 2 rows), so a Tabla/Gráfico toggle appears (task 0021).
    // Switching to Gráfico lazy-loads the Recharts chart; the table view is the default.
    await userEvent.click(screen.getByRole("button", { name: /gráfico/i }));
    expect(await screen.findByTestId("result-chart")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /tabla/i }));
    expect(screen.getByRole("table")).toBeInTheDocument();

    const chatCall = fetchMock.mock.calls.find((c) => String(c[0]) === "/chat");
    expect(chatCall).toBeDefined();
    const init = chatCall?.[1] as RequestInit;
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer tok-abc");
    const body = JSON.parse(init.body as string);
    expect(body.question).toMatch(/facturación total por ruta/);
    expect(body.history).toEqual([]);

    // 👍 on the answer posts feedback for the streamed message id (task 0020).
    const thumbUp = await screen.findByRole("button", { name: /buena respuesta/i });
    await userEvent.click(thumbUp);
    const fb = fetchMock.mock.calls.find((c) => String(c[0]) === "/feedback");
    if (!fb) throw new Error("expected a /feedback POST");
    expect(JSON.parse((fb[1] as RequestInit).body as string)).toEqual({
        message_id: "msg-9",
        rating: 1,
    });
    // The chosen rating is highlighted so the user sees it registered (task 0027).
    expect(thumbUp).toHaveAttribute("data-submitted", "true");
    expect(screen.getByRole("button", { name: /mala respuesta/i })).not.toHaveAttribute(
        "data-submitted",
    );
});
