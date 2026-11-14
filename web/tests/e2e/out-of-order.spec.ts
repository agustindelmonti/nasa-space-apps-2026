import { expect, test } from "@playwright/test";

// An older /evaluate response that arrives after a newer one must not replace it.
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", "base64");

test("respuestas fuera de orden: only the latest slider value lands", async ({ page }) => {
  await page.route(/tiles\.maps\.eox\.at|gibs\.earthdata\.nasa\.gov/, (r) => r.fulfill({ body: PNG, contentType: "image/png" }));
  const hashes: Record<string, string> = {};
  // Delay the response for lambda = 0.4 so it comes back after the one for 0.5.
  await page.route(/\/api\/v1\/evaluate$/, async (route) => {
    const body = JSON.parse(route.request().postData() ?? "{}");
    const lambda = body.overrides?.risk_aversion;
    const res = await route.fetch();
    if (lambda !== undefined) hashes[String(lambda)] = res.headers()["x-input-hash"];
    if (lambda === 0.4) await new Promise((r) => setTimeout(r, 1500));
    await route.fulfill({ response: res }).catch(() => undefined); // aborted by the page: fine
  });
  await page.goto("/");
  await expect(page.locator("li.row")).toHaveCount(5, { timeout: 20_000 }); // first load compiles on the Vite dev server

  const slider = page.locator("#slider-lambda");
  await slider.focus();
  await page.keyboard.press("ArrowRight"); // 0.4, slow
  await expect.poll(() => hashes["0.4"]).toBeTruthy();
  await page.keyboard.press("ArrowRight"); // 0.5, fast
  await expect.poll(() => hashes["0.5"]).toBeTruthy();
  await expect(page.locator("section.rank")).toHaveAttribute("data-input-hash", hashes["0.5"]);
  await page.waitForTimeout(1800); // the slow 0.4 response would have landed by now
  await expect(page.locator("section.rank")).toHaveAttribute("data-input-hash", hashes["0.5"]);
  await expect(page.locator('[data-slider="lambda"] [data-value]')).toHaveText("0,5");
});
