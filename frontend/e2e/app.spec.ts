import { expect, test } from "@playwright/test";

// A unique email per run — the app store (Postgres) persists users across runs.
function uniqueEmail(tag: string): string {
    return `e2e-${tag}-${Date.now()}@example.com`;
}

// The whole product journey against the live stack: auth → agent (SSE) → structured result + chart →
// feedback → multi-turn → logout → re-login restores the persisted conversation.
test("full journey: register → ask → chart → feedback → multi-turn → re-login restores history", async ({
    page,
}) => {
    const email = uniqueEmail("journey");
    const password = "secret12345";

    await page.goto("/");

    // --- register ---
    await page.getByRole("button", { name: /registrate/i }).click();
    await page.getByLabel("Nombre").fill("E2E User");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Contraseña").fill(password);
    await page.getByRole("button", { name: /crear cuenta/i }).click();
    await expect(page.getByRole("heading", { name: /qué querés saber/i })).toBeVisible();

    // --- ask a question → tool steps + structured result table (SSE streamed through the proxy) ---
    await page.getByRole("button", { name: /facturación total por ruta/i }).click();
    await expect(page.getByText(/Consulté la base de datos/)).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole("table")).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "origin" })).toBeVisible();

    // --- toggle to the chart (lazy-loaded Recharts) ---
    await page.getByRole("button", { name: "Gráfico" }).click();
    await expect(page.getByTestId("result-chart")).toBeVisible();

    // --- feedback on the answer (persists to Postgres) ---
    await page.getByRole("button", { name: /buena respuesta/i }).click();

    // --- multi-turn follow-up: a second answer joins the same thread ---
    const composer = page.getByRole("textbox", { name: "Message input" });
    await composer.fill("y por chofer?");
    await composer.press("Enter");
    await expect(page.getByText("y por chofer?")).toBeVisible();
    await expect(page.getByText(/Consulté la base de datos/)).toHaveCount(2, { timeout: 20_000 });

    // Regression guard: a multi-turn conversation must NOT run the layout away. The thread scrolls
    // internally, so the document height stays ~one viewport — not the 100000s of px the unclamped
    // autoscroll spacer produced before the height cascade was pinned. `toBeVisible` above never caught
    // this because it ignores runaway height; assert an explicit bound.
    await page.waitForTimeout(1000); // let any layout loop manifest
    const docHeight = await page.evaluate(() => document.documentElement.scrollHeight);
    const viewportH = page.viewportSize()?.height ?? 720;
    expect(docHeight).toBeLessThan(viewportH * 3);

    // --- logout → re-login → the conversation is restored from the store ---
    await page.getByRole("button", { name: /salir/i }).click();
    await expect(page.getByRole("button", { name: /entrar/i })).toBeVisible();
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Contraseña").fill(password);
    await page.getByRole("button", { name: /entrar/i }).click();

    // The sidebar (navigation) lists the saved conversation; opening it reloads its messages.
    const saved = page
        .getByRole("navigation")
        .getByRole("button", { name: /facturación total por ruta/i });
    await expect(saved).toBeVisible();
    await saved.click();
    await expect(page.getByText("y por chofer?")).toBeVisible();
    // task 0041: the reloaded turn rebuilds the SQL step + result table (from persisted tool_data),
    // not just the prose — so a reopened conversation looks like it did live, not empty/broken.
    await expect(page.getByText(/Consulté la base de datos/).first()).toBeVisible();
    await expect(page.getByRole("table").first()).toBeVisible();
});

// Register validation (task 0023): a too-short password reaches the server, which returns 422; the SPA
// surfaces the friendly message instead of a raw status. (Invalid emails are blocked by the native
// type="email" field before submit, and by backend unit tests.)
test("register surfaces a validation error for a short password", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: /registrate/i }).click();
    await page.getByLabel("Nombre").fill("Shorty");
    await page.getByLabel("Email").fill(uniqueEmail("short"));
    await page.getByLabel("Contraseña").fill("short"); // 5 chars < min 8
    await page.getByRole("button", { name: /crear cuenta/i }).click();
    await expect(page.getByText(/al menos 8 caracteres/i)).toBeVisible();
});

// Mobile responsiveness (task 0026): the sidebar is an off-canvas drawer toggled by a hamburger, not a
// squished fixed column. Assert the geometry — the drawer sits off-screen (negative x) until opened.
test("mobile: the sidebar is an off-canvas drawer toggled by the hamburger", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 780 });
    await page.goto("/");
    await page.getByRole("button", { name: /registrate/i }).click();
    await page.getByLabel("Nombre").fill("Mobile");
    await page.getByLabel("Email").fill(uniqueEmail("mobile"));
    await page.getByLabel("Contraseña").fill("secret12345");
    await page.getByRole("button", { name: /crear cuenta/i }).click();
    await expect(page.getByRole("heading", { name: /qué querés saber/i })).toBeVisible();

    const hamburger = page.getByRole("button", { name: /abrir conversaciones/i });
    await expect(hamburger).toBeVisible(); // hamburger only shows on mobile

    const drawerBtn = page.getByRole("button", { name: /nueva conversación/i });
    const closed = await drawerBtn.boundingBox();
    expect(closed).not.toBeNull();
    expect(closed?.x ?? 0).toBeLessThan(0); // drawer is off-canvas (translated out of view)

    await hamburger.click();
    await expect(async () => {
        const open = await drawerBtn.boundingBox();
        expect(open?.x ?? -1).toBeGreaterThanOrEqual(0); // slid into view
    }).toPass();
});
