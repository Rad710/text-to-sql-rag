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
    throw new Error(res.status === 401 ? "Email o contraseña incorrectos" : `Error ${res.status}`);
  }
  setToken(((await res.json()) as { access_token: string }).access_token);
}

export async function register(email: string, name: string, password: string): Promise<void> {
  const res = await postAuth("/auth/register", { email, name, password });
  if (!res.ok) {
    throw new Error(res.status === 409 ? "Ese email ya está registrado" : `Error ${res.status}`);
  }
  setToken(((await res.json()) as { access_token: string }).access_token);
}

/** Resolve the current user from the stored token, or null if unauthenticated/expired. */
export async function fetchMe(): Promise<AuthUser | null> {
  const token = getToken();
  if (!token) return null;
  const res = await fetch("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) {
    clearToken();
    return null;
  }
  return (await res.json()) as AuthUser;
}
