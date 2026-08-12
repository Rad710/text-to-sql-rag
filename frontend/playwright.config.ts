import { defineConfig, devices } from "@playwright/test";

// End-to-end tests (task 0023). Playwright drives a real browser against the Vite dev server (which
// proxies /chat, /auth, … to the FastAPI backend). The backend + its databases are NOT started here —
// bring the stack up first (see e2e/README or the CI `e2e` job), then run `pnpm e2e`.
export default defineConfig({
    testDir: "./e2e",
    fullyParallel: false, // one shared backend; keep runs deterministic
    workers: 1,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 1 : 0,
    reporter: process.env.CI ? "line" : "list",
    use: {
        baseURL: "http://localhost:5173",
        trace: "on-first-retry",
    },
    projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
    webServer: {
        command: "pnpm dev --port 5173",
        url: "http://localhost:5173",
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
    },
});
