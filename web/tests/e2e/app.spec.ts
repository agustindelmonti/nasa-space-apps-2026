import { expect, test, type APIRequestContext, type Page, type Response } from "@playwright/test";

// These tests run against the real API (engine over cached NASA data), started by the
// Playwright webServer. Expected orders are asked to the same API, never hardcoded.
const API = "http://127.0.0.1:8000/api/v1";

// 1x1 transparent PNG: tiles are stubbed so the tests do not depend on EOX or GIBS.
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", "base64");
const gibsRequests: string[] = [];

const isEvaluate = (r: Response) => r.url().endsWith("/api/v1/evaluate") && r.request().method() === "POST" && r.ok();
const bodyOf = (r: Response) => JSON.parse(r.request().postData() ?? "{}");

/** Opens the page and returns the X-Input-Hash of the first evaluation. */
async function open(page: Page): Promise<string> {
  await page.route(/tiles\.maps\.eox\.at/, (r) => r.fulfill({ body: PNG, contentType: "image/png" }));
  await page.route(/gibs\.earthdata\.nasa\.gov/, (r) => {
    gibsRequests.push(r.request().url());
    return r.fulfill({ body: PNG, contentType: "image/png" });
  });
  const first = page.waitForResponse(isEvaluate);
  await page.goto("/");
  const res = await first;
  await expect(page.locator("li.row")).toHaveCount(5, { timeout: 20_000 }); // first load compiles on the Vite dev server
  return res.headers()["x-input-hash"];
}

const order = (page: Page) => page.locator("li.row").evaluateAll((els) => els.map((e) => (e as HTMLElement).dataset.id));

async function apiOrder(request: APIRequestContext, actor: string): Promise<string[]> {
  const res = await request.post(`${API}/evaluate`, { data: { actor } });
  expect(res.ok()).toBe(true);
  const body = await res.json();
  return [...body.engine_output.results].sort((a, b) => a.rank - b.rank).map((r: { rotation_id: string }) => r.rotation_id);
}

test("loads real engine results with the fixed legends and no horizontal scroll", async ({ page }) => {
  await open(page);
  await expect(page.getByText("Apoya, no reemplaza al agrónomo.")).toBeVisible();
  await expect(page.getByText("Escenarios históricos, no predicción.")).toBeVisible();
  await expect(page.getByText(/Datos de ejemplo|Modo demo sin conexión/)).toHaveCount(0);
  await expect(page.locator('li[data-id="R_SOY_COVER"] .rot-name')).toHaveText("Soja con vicia de servicio");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});

test("Propietario -> Banco changes the order as the engine ranks it, with up/down marks", async ({ page, request }) => {
  await open(page);
  const owner = await apiOrder(request, "OWNER");
  const bank = await apiOrder(request, "BANK");
  expect(bank).not.toEqual(owner);
  expect(await order(page)).toEqual(owner);
  await expect(page.locator("li.row.current")).toContainText("actual");

  await page.getByRole("button", { name: "Banco" }).click();
  await expect.poll(() => order(page)).toEqual(bank);
  await expect(page.locator(`li[data-id="${bank[0]}"]`)).toHaveClass(/first/);
  await expect(page.locator(".move[data-move]").first()).toHaveText(/[▲▼] \d/);
});

test("moving lambda sends overrides, changes the X-Input-Hash and 'volver al perfil' restores it", async ({ page }) => {
  const initial = await open(page);
  await page.getByRole("button", { name: /Ajustar perfil/ }).click(); // folded by default
  const slider = page.locator("#slider-lambda");
  await expect(page.locator('[data-slider="lambda"] [data-value]')).toHaveText("0,3");

  const moved = page.waitForResponse((r) => isEvaluate(r) && bodyOf(r).overrides?.risk_aversion !== undefined);
  await slider.focus();
  for (let i = 0; i < 5; i++) await page.keyboard.press("ArrowRight");
  await expect(page.locator('[data-slider="lambda"] [data-value]')).toHaveText("0,8");
  const res = await moved;
  expect(bodyOf(res).overrides).toEqual({ risk_aversion: 0.8 }); // debounced: one request with the final value
  const hash = res.headers()["x-input-hash"];
  expect(hash).toBeTruthy();
  expect(hash).not.toBe(initial);
  await expect(page.locator("section.rank")).toHaveAttribute("data-input-hash", hash);

  await page.getByRole("button", { name: "Volver al perfil" }).click();
  await expect(page.locator("section.rank")).toHaveAttribute("data-input-hash", initial);
  await expect(page.getByRole("button", { name: "Volver al perfil" })).toHaveCount(0);
});

test("year class and presentation preferences go to /evaluate; the table follows display_order", async ({ page }) => {
  await open(page);
  const dry = page.waitForResponse((r) => isEvaluate(r) && bodyOf(r).year_class_filter === "DRY");
  await page.getByRole("button", { name: "Años secos" }).click();
  await dry;
  await expect(page.getByRole("button", { name: "Años secos" })).toHaveAttribute("aria-pressed", "true");

  const pref = page.waitForResponse((r) => isEvaluate(r) && (bodyOf(r).display_preferences ?? []).includes("WATER_SAFE_FIRST"));
  await page.getByRole("button", { name: "Primero las que no son riesgosas en agua" }).click();
  const body = await (await pref).json();
  await expect.poll(() => order(page)).toEqual(body.display_order);
});

test("ineligible rotations say why, in Spanish, and the low-eligible warning is visible", async ({ page }) => {
  await open(page);
  await page.getByRole("button", { name: "Arrendatario" }).click();
  await expect(page.locator('[data-warning="LOW_ELIGIBLE_COUNT"]')).toContainText("menos de 3 rotaciones elegibles");
  const out = page.locator('li.row[data-eligible="false"]');
  await expect(out.first()).toBeVisible();
  await expect(out.first().locator(".out")).toHaveText("No elegible");
  await expect(out.first().locator(".why")).toContainText("supera el capital de trabajo disponible");
});

test("reduced motion: reorders without animation and keeps the marks", async ({ page, request }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await open(page);
  const bank = await apiOrder(request, "BANK");
  await page.getByRole("button", { name: "Banco" }).click();
  await expect.poll(() => order(page)).toEqual(bank);
  const running = await page.evaluate(() => document.getAnimations().filter((a) => a.playState === "running").length);
  expect(running).toBe(0);
  await expect(page.locator(".move[data-move]").first()).toHaveText(/[▲▼] \d/);
});

test("campaign strips: 24 months for each of the 5 catalog rotations and a visible legend", async ({ page }) => {
  await open(page);
  const strips = page.locator(".strip");
  await expect(strips).toHaveCount(5);
  for (let i = 0; i < 5; i++) await expect(strips.nth(i).locator("i")).toHaveCount(24);
  await expect(page.locator('li[data-id="R_SOY_MONO"] .strip')).toHaveAttribute("aria-label", /suelo desnudo/);
  await expect(page.locator('li[data-id="R_SOY_COVER"] .strip')).toHaveAttribute("aria-label", /vicia/);
  await expect(page.locator('li[data-id="R_MAIZE_SOY_COVER"] .strip')).toHaveAttribute("aria-label", /centeno/);
  const legend = page.getByRole("list", { name: "Leyenda de la franja" });
  await expect(legend).toBeVisible();
  await expect(legend).toContainText("Helada");
});

test("GIBS layers are offered and request tiles with the configured identifier and date", async ({ page }) => {
  await open(page);
  for (const name of ["SMAP raíces", "NDVI MODIS", "Lluvia IMERG"]) await expect(page.getByRole("button", { name })).toBeVisible();
  gibsRequests.length = 0;
  await page.getByRole("button", { name: "NDVI MODIS" }).click();
  await expect.poll(() => gibsRequests.length).toBeGreaterThan(0);
  expect(gibsRequests[0]).toContain("/wmts/epsg3857/best/MODIS_Terra_NDVI_8Day/default/2026-11-09/GoogleMapsCompatible_Level9/");
  await expect(page.locator("#layerinfo")).toContainText("250 m");
  await page.getByRole("button", { name: "SMAP raíces" }).click();
  await expect(page.locator("#layerinfo")).toContainText("~9 km");
  await expect(page.locator("#layerinfo")).toContainText("no mide el lote");
});

test("provenance tooltip opens with the keyboard and shows dataset, variable, period and resolution", async ({ page }) => {
  await open(page);
  const badge = page.locator('[data-cell="smap"] .badge');
  await badge.focus();
  const tip = page.locator('[data-cell="smap"] [role="tooltip"]');
  await expect(tip).toBeVisible();
  await expect(tip).toContainText("SMAP L4");
  await expect(tip).toContainText("sm_rootzone");
  await expect(tip).toContainText("10/11/2026");
  await expect(tip).toContainText("~9 km");
  await page.keyboard.press("Escape");
  await expect(tip).toBeHidden();

  await page.getByRole("button", { name: /Ajustar perfil/ }).click(); // folded by default
  const sup = page.locator(".params .badge");
  await sup.focus();
  await expect(page.locator('.params [role="tooltip"]')).toContainText("pendiente de validar con AFA");
});
