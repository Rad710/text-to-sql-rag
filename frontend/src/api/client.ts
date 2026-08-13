// The one HTTP entry point for authenticated calls (decision 0013). Attaches the in-memory access
// token, and on a 401 transparently rotates it once via /auth/refresh and retries; if that fails, it
// signs out. Self-contained (imports only the store) so it never cycles with api/auth.

import { useSession } from "@/stores/session";

// Single-flight: concurrent callers (parallel 401s, a double-invoked StrictMode effect, multiple tabs
// racing) share ONE in-flight /auth/refresh instead of each rotating the token — which would orphan
// tokens and could trip server-side reuse detection and spuriously sign the user out.
let refreshInFlight: Promise<boolean> | null = null;

async function doRefresh(): Promise<boolean> {
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

/** Exchange the stored refresh token for a fresh pair (deduped). Returns true on success. */
export function tryRefresh(): Promise<boolean> {
    if (!refreshInFlight) {
        refreshInFlight = doRefresh().finally(() => {
            refreshInFlight = null;
        });
    }
    return refreshInFlight;
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
