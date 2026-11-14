// Fails if any hex color used in web/src is not declared in the DESIGN.md frontmatter.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const design = readFileSync(resolve(here, "../../DESIGN.md"), "utf8");
const front = design.split(/^---$/m)[1] ?? "";
const allowed = new Set([...front.matchAll(/#[0-9a-fA-F]{6}\b/g)].map((m) => m[0].toLowerCase()));

const src = resolve(here, "../src");
const walk = (dir) =>
  readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) return f === "generated" ? [] : walk(p);
    return /\.(css|tsx?|json|html)$/.test(f) && !f.endsWith(".test.ts") ? [p] : [];
  });

const problems = [];
for (const file of walk(src)) {
  const text = readFileSync(file, "utf8");
  for (const m of text.matchAll(/#[0-9a-fA-F]{3,8}\b/g)) {
    const hex = m[0].toLowerCase();
    if (hex.length !== 7 || !allowed.has(hex)) problems.push(`${relative(src, file)}: ${m[0]}`);
  }
}

if (problems.length) {
  console.error(`Colors outside DESIGN.md frontmatter (${problems.length}):\n  ${problems.join("\n  ")}`);
  process.exit(1);
}
console.log(`check:tokens ok (${allowed.size} colors allowed)`);
