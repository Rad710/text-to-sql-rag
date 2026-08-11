import { afterEach, expect, test, vi } from "vitest";

import { fetchMe, isTokenExpired } from "./auth";

/** A JWT with the given `exp` (seconds); header/signature are irrelevant to the client-side check. */
function jwt(expSeconds: number): string {
  return `h.${btoa(JSON.stringify({ exp: expSeconds }))}.s`;
}

const now = () => Math.floor(Date.now() / 1000);

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

test("isTokenExpired: past exp → true, future exp → false", () => {
  expect(isTokenExpired(jwt(now() - 60))).toBe(true);
  expect(isTokenExpired(jwt(now() + 3600))).toBe(false);
});

test("isTokenExpired: an unparseable token → false (let the server decide)", () => {
  expect(isTokenExpired("tok-abc")).toBe(false);
  expect(isTokenExpired("a.b.c")).toBe(false);
  expect(isTokenExpired("")).toBe(false);
});

test("fetchMe: an expired token resolves to null, clears the token, and makes no request", async () => {
  localStorage.setItem("dyr_token", jwt(now() - 60));
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);

  expect(await fetchMe()).toBeNull();
  expect(fetchMock).not.toHaveBeenCalled(); // no /auth/me → no console 401
  expect(localStorage.getItem("dyr_token")).toBeNull();
});

test("fetchMe: no token → null, no request", async () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  expect(await fetchMe()).toBeNull();
  expect(fetchMock).not.toHaveBeenCalled();
});
