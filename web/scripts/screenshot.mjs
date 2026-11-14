// Takes a screenshot of the running preview (npm run preview).
// Usage: [BASE_URL=..] [SCROLL_TO=selector] node scripts/screenshot.mjs [width] [height] [out] [fullPage 0|1]
import { chromium } from "@playwright/test";

const [w = "1440", h = "900", out = "docs/screenshot.png", full = "0"] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: Number(w), height: Number(h) } });
const errors = [];
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(process.env.BASE_URL ?? "http://localhost:4173/");
await page.waitForSelector(".row");
await page.waitForTimeout(3000);
// SCROLL_TO=<selector> scrolls that element to the top first (the map is sticky, so it stays in view).
if (process.env.SCROLL_TO) {
  await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (el) window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 16);
  }, process.env.SCROLL_TO);
  await page.waitForTimeout(500);
}
await page.screenshot({ path: out, fullPage: full === "1" });
if (errors.length) console.log("console errors:", errors);
await browser.close();
