import { afterEach, expect, test, vi } from "vitest";
import { login } from "@/api/auth";
import { apiFetch } from "@/api/client";
import { useSession } from "@/stores/session";

function resetSession(): void {
    useSession.setState({
        accessToken: null,
        refreshToken: null,
        user: null,
        status: "loading",
        conversationId: null,
        lastAssistantMessageId: null,
    });
}

afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    resetSession();
});

function json(data: unknown, status = 200): Response {
    return { ok: status < 400, status, json: async () => data } as unknown as Response;
}

test("login stores the token pair + user and marks the session authenticated", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url === "/auth/login") {
            return Promise.resolve(json({ access_token: "acc-1", refresh_token: "ref-1" }));
        }
        return Promise.resolve(json({ id: "u1", email: "a@b.com", name: "Ana" })); // /auth/me
    });
    vi.stubGlobal("fetch", fetchMock);

    await login("a@b.com", "pw");

    const s = useSession.getState();
    expect(s.accessToken).toBe("acc-1");
    expect(s.refreshToken).toBe("ref-1");
    expect(s.user).toEqual({ id: "u1", email: "a@b.com", name: "Ana" });
    expect(s.status).toBe("authenticated");
});

test("apiFetch refreshes once on a 401 and retries with the new access token", async () => {
    useSession.setState({ accessToken: "stale", refreshToken: "ref-1" });
    const seen: string[] = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url === "/auth/refresh") {
            return Promise.resolve(json({ access_token: "acc-2", refresh_token: "ref-2" }));
        }
        // The /me call: first attempt (stale token) 401s, the retry (acc-2) succeeds.
        const auth = (init?.headers as Record<string, string> | undefined)?.Authorization;
        seen.push(auth ?? "");
        return Promise.resolve(auth === "Bearer acc-2" ? json({ ok: true }) : json({}, 401));
    });
    vi.stubGlobal("fetch", fetchMock);

    const res = await apiFetch("/auth/me");

    expect(res.ok).toBe(true);
    expect(seen).toEqual(["Bearer stale", "Bearer acc-2"]); // refreshed + retried once
    expect(useSession.getState().accessToken).toBe("acc-2");
    expect(useSession.getState().refreshToken).toBe("ref-2");
});

test("apiFetch signs out when the refresh also fails", async () => {
    useSession.setState({ accessToken: "stale", refreshToken: "ref-1", status: "authenticated" });
    // Both the request and /auth/refresh 401.
    const fetchMock = vi.fn(() => Promise.resolve(json({}, 401)));
    vi.stubGlobal("fetch", fetchMock);

    const res = await apiFetch("/conversations");

    expect(res.status).toBe(401);
    const s = useSession.getState();
    expect(s.accessToken).toBeNull();
    expect(s.refreshToken).toBeNull();
    expect(s.status).toBe("anonymous");
});
