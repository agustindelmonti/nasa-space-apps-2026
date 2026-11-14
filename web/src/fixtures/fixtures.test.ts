import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import Ajv2020 from "ajv/dist/2020";
import addFormats from "ajv-formats";
import { describe, expect, it } from "vitest";

const root = resolve(__dirname, "../../..");
const load = (p: string) => JSON.parse(readFileSync(resolve(root, p), "utf8"));

const outputSchema = load("schemas/engine_output.schema.json");
const inputSchema = load("schemas/engine_input.schema.json");

const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
ajv.addSchema(inputSchema, "engine_input");
const validateOutput = ajv.compile(outputSchema);
const def = (name: string) => ajv.getSchema(`engine_input#/$defs/${name}`)!;

const outputs = ["demo", "owner", "tenant", "coop", "bank"];

describe("engine output fixtures", () => {
  for (const name of outputs) {
    it(`engine_output.${name}.json validates against schemas/engine_output.schema.json`, () => {
      const data = load(`web/src/fixtures/engine_output.${name}.json`);
      const ok = validateOutput(data);
      expect(validateOutput.errors ?? []).toEqual([]);
      expect(ok).toBe(true);
      expect(data.results).toHaveLength(4);
      expect(data.results.filter((r: { is_current: boolean }) => r.is_current)).toHaveLength(1);
    });
  }

  it("the four actor fixtures carry different orders", () => {
    const orders = outputs.slice(1).map((n) =>
      load(`web/src/fixtures/engine_output.${n}.json`)
        .results.map((r: { rotation_id: string }) => r.rotation_id)
        .join(","),
    );
    expect(new Set(orders).size).toBe(4);
  });

  it("the validator rejects a broken output (sanity check)", () => {
    const data = load("web/src/fixtures/engine_output.demo.json");
    data.results[0].breakdown!.total.unit = "USD";
    delete data.results[1].loss_years;
    expect(validateOutput(data)).toBe(false);
  });

  it("marks itself as example data", () => {
    const data = load("web/src/fixtures/engine_output.demo.json");
    expect(data.engine_version).toContain("ejemplo");
  });
});

describe("demo context fixture", () => {
  const ctx = load("web/src/fixtures/demo_context.json");

  it("plot validates against the Plot definition", () => {
    expect(def("Plot")(ctx.plot), JSON.stringify(def("Plot").errors)).toBe(true);
  });

  it("rotations validate against the Rotation definition", () => {
    for (const r of ctx.rotations) expect(def("Rotation")(r), JSON.stringify(def("Rotation").errors)).toBe(true);
  });

  it("profiles validate against the ActorProfile definition", () => {
    const ids = ctx.profiles.map((p: { profile_id: string }) => p.profile_id);
    expect(ids).toEqual(["OWNER", "TENANT", "COOP", "BANK"]);
    for (const p of ctx.profiles) expect(def("ActorProfile")(p), JSON.stringify(def("ActorProfile").errors)).toBe(true);
  });

  it("water panel values validate against the PValue definition", () => {
    for (const cell of Object.values(ctx.water_panel) as { value: unknown }[]) {
      expect(def("PValue")(cell.value), JSON.stringify(def("PValue").errors)).toBe(true);
    }
  });
});
