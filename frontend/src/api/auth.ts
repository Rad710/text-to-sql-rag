// Auth client (decision 0009): JWT stored in localStorage, sent as `Authorization: Bearer …`.
// The token lives here (not in React state) so the assistant-ui runtime adapter can read it at
// request time without prop-drilling.

const TOKEN_KEY = "dyr_token";

export type AuthUser = { id: string; email: string; name: string };

export function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}

function setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
}

// Seam so a 401 during a request (e.g. the token expired mid-session) can bounce the user back to the
// login screen. The runtime adapter calls notifyUnauthorized(); App registers the handler.
let unauthorizedHandler: (() => void) | null = null;

export function onUnauthorized(handler: (() => void) | null): void {
    unauthorizedHandler = handler;
}

export function notifyUnauthorized(): void {
    clearToken();
    unauthorizedHandler?.();
}

/**
 * True only when the JWT is definitely past its `exp`. Used to skip the `/auth/me` probe for an
 * expired token — otherwise the browser logs a (harmless but noisy) 401 on every load for a returning
 * user whose token lapsed. A token we can't parse returns `false`: we don't guess, we let the server
 * decide (keeps the check conservative and unit-testable without a real JWT).
 */
export function isTokenExpired(token: string): boolean {
    const payload = token.split(".")[1];
    if (!payload) return false;
    try {
        const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
        const exp = (JSON.parse(json) as { exp?: number }).exp;
        return typeof exp === "number" && exp * 1000 <= Date.now();
    } catch {
        return false;
    }
}

async function postAuth(path: string, body: Record<string, string>): Promise<Response> {
    return fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

export async function login(email: string, password: string): Promise<void> {
    const res = await postAuth("/auth/login", { email, password });
    if (!res.ok) {
        throw new Error(
            res.status === 401 ? "Email o contraseña incorrectos" : `Error ${res.status}`,
        );
    }
    setToken(((await res.json()) as { access_token: string }).access_token);
}

export async function register(email: string, name: string, password: string): Promise<void> {
    const res = await postAuth("/auth/register", { email, name, password });
    if (!res.ok) {
        if (res.status === 409) throw new Error("Ese email ya está registrado");
        // 422 = the API rejected the email format or the password length (min 8).
        if (res.status === 422)
            throw new Error("Revisá el email y que la contraseña tenga al menos 8 caracteres");
        throw new Error(`Error ${res.status}`);
    }
    setToken(((await res.json()) as { access_token: string }).access_token);
}

/** Resolve the current user from the stored token, or null if unauthenticated/expired. */
export async function fetchMe(): Promise<AuthUser | null> {
    const token = getToken();
    if (!token) return null;
    // Skip the round-trip (and its console 401) if the token is already expired.
    if (isTokenExpired(token)) {
        clearToken();
        return null;
    }
    const res = await fetch("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) {
        clearToken();
        return null;
    }
    return (await res.json()) as AuthUser;
}
