import { expect, test, type Page } from "@playwright/test";

// The API is configured but unreachable (requests aborted): the page falls back to the
// example fixtures and says so.
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", "base64");

async function openOffline(page: Page) {
  await page.route(/127\.0\.0\.1:8000/, (r) => r.abort("connectionrefused"));
  await page.route(/tiles\.maps\.eox\.at|gibs\.earthdata\.nasa\.gov/, (r) => r.fulfill({ body: PNG, contentType: "image/png" }));
  await page.goto("/");
  await expect(page.locator("li.row")).toHaveCount(4, { timeout: 20_000 }); // first load compiles on the Vite dev server
}

const order = (page: Page) => page.locator("li.row").evaluateAll((els) => els.map((e) => (e as HTMLElement).dataset.id));

test("API down: offline demo notice, fixture ranking and actor reorder still work", async ({ page }) => {
  await openOffline(page);
  await expect(page.locator('[data-mode="offline"]')).toContainText("Modo demo sin conexión");
  expect(await order(page)).toEqual(["R_MAIZE_SOY_COVER", "R_WHEAT_SOY2_MAIZE", "R_MAIZE_SOY", "R_SOY_MONO"]);

  await page.getByRole("button", { name: "Arrendatario" }).click();
  await expect.poll(() => order(page)).toEqual(["R_SOY_MONO", "R_WHEAT_SOY2_MAIZE", "R_MAIZE_SOY", "R_MAIZE_SOY_COVER"]);
  await expect(page.locator('li[data-id="R_SOY_MONO"] .move')).toHaveText("▲ 3");
  await expect(page.locator('li[data-id="R_MAIZE_SOY_COVER"] .move')).toHaveText("▼ 3");
});

test("API down: sliders and options are off because the fixtures cannot re-evaluate", async ({ page }) => {
  await openOffline(page);
  await expect(page.locator("#slider-lambda")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Años secos" })).toBeDisabled();
  await expect(page.getByText("Los ajustes necesitan conexión con el motor.")).toBeVisible();
});
