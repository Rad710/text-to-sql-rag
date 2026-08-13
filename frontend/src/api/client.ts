// The one HTTP entry point for authenticated calls (decision 0013). Attaches the in-memory access
// token, and on a 401 transparently rotates it once via /auth/refresh and retries; if that fails, it
// signs out. Self-contained (imports only the store) so it never cycles with api/auth.

import { useSession } from "@/stores/session";

/** Exchange the stored refresh token for a fresh pair. Returns true on success. */
export async function tryRefresh(): Promise<boolean> {
    const { refreshToken } = useSession.getState();
    if (!refreshToken) return false;
    const res = await fetch("/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const { access_token, refresh_token } = (await res.json()) as {
        access_token: string;
        refresh_token: string;
    };
    useSession.getState().setTokens(access_token, refresh_token);
    return true;
}

/** `fetch` with the Bearer access token attached; refreshes once on a 401, else signs out. */
export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
    const authed = (): RequestInit => {
        const { accessToken } = useSession.getState();
        return {
            ...init,
            headers: {
                ...init.headers,
                ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
            },
        };
    };

    let res = await fetch(input, authed());
    if (res.status === 401) {
        if (await tryRefresh()) {
            res = await fetch(input, authed());
            if (res.status !== 401) return res;
        }
        useSession.getState().signOut();
    }
    return res;
}
