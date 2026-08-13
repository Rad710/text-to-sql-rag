// Auth client (decisions 0009, 0013). Login/register receive an access + refresh pair; the access
// token is held in memory and the refresh token persisted, both in the session store. There is no
// token plumbing in components — apiFetch attaches the token and refreshes it on demand.

import { apiFetch, tryRefresh } from "@/api/client";
import { type AuthUser, useSession } from "@/stores/session";

export type { AuthUser };

type TokenPair = { access_token: string; refresh_token: string };

async function postJson(path: string, body: Record<string, string>): Promise<Response> {
    return fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

async function completeSignIn(res: Response): Promise<void> {
    const { access_token, refresh_token } = (await res.json()) as TokenPair;
    useSession.getState().setTokens(access_token, refresh_token);
    useSession.getState().setUser(await fetchMe());
}

// Errors carry an i18n key (not a message); the form translates it via t(). Keeps this layer
// language-agnostic (task 0040).
export async function login(email: string, password: string): Promise<void> {
    const res = await postJson("/auth/login", { email, password });
    if (!res.ok) {
        throw new Error(res.status === 401 ? "errors.invalidCredentials" : "errors.generic");
    }
    await completeSignIn(res);
}

export async function register(email: string, name: string, password: string): Promise<void> {
    const res = await postJson("/auth/register", { email, name, password });
    if (!res.ok) {
        if (res.status === 409) throw new Error("errors.emailTaken");
        // 422 = the API rejected the email format or the password length (min 8).
        if (res.status === 422) throw new Error("errors.invalidInput");
        throw new Error("errors.generic");
    }
    await completeSignIn(res);
}

/** Revoke the refresh token server-side (best-effort) and clear the local session. */
export async function logout(): Promise<void> {
    const { refreshToken } = useSession.getState();
    if (refreshToken) {
        try {
            await postJson("/auth/logout", { refresh_token: refreshToken });
        } catch {
            // Network hiccup on logout: still clear the client session below.
        }
    }
    useSession.getState().signOut();
}

/** Resolve the current user for the active session, or null if unauthenticated. */
export async function fetchMe(): Promise<AuthUser | null> {
    const res = await apiFetch("/auth/me");
    return res.ok ? ((await res.json()) as AuthUser) : null;
}

/** On app load: if a refresh token survived, rotate it into an access token and load the user. */
export async function bootstrapSession(): Promise<void> {
    const store = useSession.getState();
    if (!store.refreshToken) {
        store.setStatus("anonymous");
        return;
    }
    if (!(await tryRefresh())) {
        store.signOut();
        return;
    }
    store.setUser(await fetchMe());
}
