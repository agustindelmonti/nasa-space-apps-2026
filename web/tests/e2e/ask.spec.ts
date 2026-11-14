import { expect, test, type Page, type Response } from "@playwright/test";

// "Preguntale a Rastrojo" and the five-section card, against the real API.
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", "base64");
const isPost = (path: string) => (r: Response) => r.url().endsWith(path) && r.request().method() === "POST" && r.ok();

async function open(page: Page) {
  await page.route(/tiles\.maps\.eox\.at|gibs\.earthdata\.nasa\.gov/, (r) => r.fulfill({ body: PNG, contentType: "image/png" }));
  await page.goto("/");
  await expect(page.locator("li.row")).toHaveCount(5, { timeout: 20_000 }); // first load compiles on the Vite dev server
}

test("asking '¿Cuál me conviene?' answers with a trace, a mode badge and keeps the state", async ({ page }) => {
  await open(page);
  await page.getByRole("button", { name: "Preguntale a Rastrojo" }).click();
  const panel = page.getByRole("complementary", { name: "Preguntale a Rastrojo" });
  await expect(panel).toBeVisible();

  const first = page.waitForResponse(isPost("/api/v1/ask"));
  await panel.getByLabel("Tu pregunta").fill("¿Cuál me conviene?");
  await panel.getByRole("button", { name: "Enviar" }).click();
  const res = await first;
  const body = await res.json();
  expect(body.trace.length).toBeGreaterThan(0);

  const bot = panel.locator('[data-role="bot"]').last();
  await expect(bot.locator(".bubble")).toContainText("USD/ha");
  await expect(panel.locator(".mode")).toHaveText("por reglas");
  await bot.getByText("Cómo llegué a esto").click();
  await expect(bot.locator(".trace .tool").first()).toHaveText(body.trace[0].tool);
  await expect(bot.locator(".trace .hash").first()).toContainText(body.trace[0].input_hash.slice(0, 12));

  // Next turn from a suggestion sends back the state the API returned.
  const second = page.waitForResponse(isPost("/api/v1/ask"));
  await panel.locator(".suggest button").first().click();
  const sent = JSON.parse((await second).request().postData() ?? "{}");
  expect(sent.state).toEqual(body.state);
  await expect(panel.locator('[data-role="bot"]')).toHaveCount(2);
});

test("WhatsApp simulator shows the reply split in messages from /chat/simulate", async ({ page }) => {
  await open(page);
  await page.getByRole("button", { name: "Preguntale a Rastrojo" }).click();
  const panel = page.getByRole("complementary", { name: "Preguntale a Rastrojo" });
  await panel.getByRole("button", { name: "Simulador WhatsApp" }).click();
  const sim = page.waitForResponse(isPost("/api/v1/chat/simulate"));
  await panel.getByLabel("Tu pregunta").fill("¿Cuál me conviene?");
  await panel.getByRole("button", { name: "Enviar" }).click();
  const body = await (await sim).json();
  const messages = (body.messages as string[]).map((m) => m.trim()).filter(Boolean);
  await expect(panel.locator('[data-role="bot"] .bubble')).toHaveCount(messages.length);
});

test("the evidence panel shows the five-section card of the selected rotation", async ({ page }) => {
  await open(page);
  const card = page.locator(".card5");
  await expect(card).toBeVisible();
  for (const s of ["Por qué", "Evidencia", "Beneficios", "Qué falta saber", "Riesgos"]) {
    // The three that matter are up front; "Evidencia" and "Beneficios" live in the detail.
    await expect(page.locator(`.evidence [data-section="${s}"] h4`)).toHaveText(s);
  }
  await page.locator('li[data-id="R_SOY_COVER"] .name-btn').click();
  await expect(card).toHaveAttribute("data-rotation", "R_SOY_COVER");
});
