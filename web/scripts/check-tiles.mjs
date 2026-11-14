// Requests one tile of each configured layer over the demo lot and expects HTTP 200.
// Run: npm run check:tiles (needs network to EOX and GIBS).
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const layers = JSON.parse(readFileSync(resolve(here, "../src/config/layers.json"), "utf8"));
const ctx = JSON.parse(readFileSync(resolve(here, "../src/fixtures/demo_context.json"), "utf8"));
const { lat, lon } = ctx.plot.location;

const tile = (z) => {
  const n = 2 ** z;
  const r = (lat * Math.PI) / 180;
  return {
    x: Math.floor(((lon + 180) / 360) * n),
    y: Math.floor(((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2) * n),
  };
};
const fill = (url, z) => {
  const { x, y } = tile(z);
  return url.replace("{z}", z).replace("{x}", x).replace("{y}", y);
};

const urls = [[layers.base.id, fill(layers.base.url, 15)]];
for (const o of layers.overlays) {
  const t = layers.gibsTemplate
    .replace("{layer}", o.gibsLayer)
    .replace("{time}", o.date)
    .replace("{tileMatrixSet}", o.tileMatrixSet)
    .replace("{ext}", o.format);
  urls.push([o.id, fill(t, o.maxNativeZoom)]);
}

let failed = 0;
for (const [id, url] of urls) {
  const res = await fetch(url);
  const bytes = (await res.arrayBuffer()).byteLength;
  console.log(`${res.status} ${id.padEnd(12)} ${bytes} B  ${url}`);
  if (res.status !== 200) failed++;
}
process.exit(failed ? 1 : 0);
