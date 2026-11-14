import { expect, test, type Page } from "@playwright/test";

// 1x1 transparent PNG: tiles are stubbed so the tests do not depend on EOX or GIBS.
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", "base64");
const gibsRequests: string[] = [];

async function open(page: Page) {
  await page.route(/tiles\.maps\.eox\.at/, (r) => r.fulfill({ body: PNG, contentType: "image/png" }));
  await page.route(/gibs\.earthdata\.nasa\.gov/, (r) => {
    gibsRequests.push(r.request().url());
    return r.fulfill({ body: PNG, contentType: "image/png" });
  });
  await page.goto("/");
  await expect(page.locator("li.row")).toHaveCount(4);
}

const order = (page: Page) => page.locator("li.row").evaluateAll((els) => els.map((e) => (e as HTMLElement).dataset.id));

test("loads with the fixed legends visible and no horizontal scroll", async ({ page }) => {
  await open(page);
  await expect(page.getByText("Apoya, no reemplaza al agrónomo.")).toBeVisible();
  await expect(page.getByText("Escenarios históricos, no predicción.")).toBeVisible();
  await expect(page.getByText(/Datos de ejemplo/)).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});

test("changing the actor reorders the ranking as the fixture says, with up/down marks", async ({ page }) => {
  await open(page);
  const owner = await order(page);
  expect(owner).toEqual(["R_MAIZE_SOY_COVER", "R_WHEAT_SOY2_MAIZE", "R_MAIZE_SOY", "R_SOY_MONO"]);
  await expect(page.locator("li.row.current")).toContainText("actual");

  await page.getByRole("button", { name: "Arrendatario" }).click();
  await expect.poll(() => order(page)).toEqual(["R_SOY_MONO", "R_WHEAT_SOY2_MAIZE", "R_MAIZE_SOY", "R_MAIZE_SOY_COVER"]);
  await expect(page.locator('li[data-id="R_SOY_MONO"] .move')).toHaveText("▲ 3");
  await expect(page.locator('li[data-id="R_MAIZE_SOY_COVER"] .move')).toHaveText("▼ 3");
  await expect(page.locator('li[data-id="R_SOY_MONO"]')).toHaveClass(/first/);
  await expect(page.getByText("Horizonte 1 año")).toBeVisible();
});

test("reduced motion: reorders without animation and keeps the marks", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await open(page);
  await page.getByRole("button", { name: "Banco" }).click();
  await expect.poll(() => order(page)).toEqual(["R_MAIZE_SOY", "R_SOY_MONO", "R_MAIZE_SOY_COVER", "R_WHEAT_SOY2_MAIZE"]);
  const running = await page.evaluate(() => document.getAnimations().filter((a) => a.playState === "running").length);
  expect(running).toBe(0);
  await expect(page.locator('li[data-id="R_MAIZE_SOY"] .move')).toHaveText("▲ 2");
});

test("campaign strips: 24 months per rotation, frost marks and a visible legend", async ({ page }) => {
  await open(page);
  const strips = page.locator(".strip");
  await expect(strips).toHaveCount(4);
  for (let i = 0; i < 4; i++) await expect(strips.nth(i).locator("i")).toHaveCount(24);
  await expect(page.locator('li[data-id="R_WHEAT_SOY2_MAIZE"] .strip i.frost')).toHaveCount(2);
  await expect(page.locator('li[data-id="R_SOY_MONO"] .strip')).toHaveAttribute("aria-label", /suelo desnudo/);
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
  await expect(tip).toContainText("01/11/2026 a 10/11/2026");
  await expect(tip).toContainText("~9 km");
  await page.keyboard.press("Escape");
  await expect(tip).toBeHidden();

  const sup = page.locator(".params .badge");
  await sup.focus();
  await expect(page.locator('.params [role="tooltip"]')).toContainText("pendiente de validar con AFA");
});
