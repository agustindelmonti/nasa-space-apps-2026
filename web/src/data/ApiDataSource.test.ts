import { describe, expect, it, vi } from "vitest";
import { ApiDataSource, ApiError } from "./ApiDataSource";
import { StaleResponseError } from "./DataSource";
import { FixtureDataSource } from "./FixtureDataSource";
import owner from "../fixtures/engine_output.owner.json";

const BASE = "http://api.test";
const PLOT = "demo-casilda";

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });

const evalBody = (hash: string, order = ["R_MAIZE_SOY", "R_SOY_MONO"]) => ({
  input_hash: hash,
  engine_version: "0.1.0",
  engine_output: { ...owner, input_hash: hash },
  rotation_names: { R_MAIZE_SOY: "Maíz / Soja", R_SOY_MONO: "Soja continua" },
  display_order: order,
});

const profilesBody = {
  profiles: [{ profile_id: "OWNER", label: "Propietario" }],
  slider_limits: { horizon_years: [1, 20], alpha: [0, 20], lambda: [0, 3] },
};
const catalogBody = { rotations: [{ rotation_id: "R_SOY_COVER", name: "Soja con vicia de servicio", campaigns: [] }] };

function deferred<T>() {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

describe("ApiDataSource", () => {
  it("reads profiles, slider limits and catalog from the API", async () => {
    const pv = { value: 0.25, unit: "m3/m3", provenance: { kind: "DERIVED", method: "x", derived_from: ["SMAP_L4"] } };
    const waterBody = {
      grace: { label: "Agua total", value: null, limitation: "sin dato" },
      smap: { label: "Raíces", value: pv, limitation: "hoy" },
      rain: { label: "Lluvia", value: { ...pv, unit: "mm", value: 597 }, limitation: "mediana" },
    };
    const assumptionsBody = {
      assumptions: [{ assumption_id: "A-ACT-06", description: "Rangos de sliders", reference: "AFA", status: "PENDING_AFA" }],
    };
    const fetch = vi.fn(async (url: RequestInfo | URL) => {
      const u = String(url);
      if (u.endsWith("/actors/profiles")) return json(profilesBody);
      if (u.endsWith("/assumptions")) return json(assumptionsBody);
      if (u.endsWith("/water-panel")) return json({ water_panel: waterBody });
      return json(catalogBody);
    });
    const src = new ApiDataSource(BASE + "/", new FixtureDataSource(), { fetch });
    const ctx = await src.getContext(PLOT);
    expect(ctx.water_panel.grace.value).toBeNull(); // the panel comes from the API, gaps included
    expect(ctx.water_panel.smap.limitation).toBe("hoy");
    expect(ctx.origin).toBe("api");
    expect(ctx.slider_limits.lambda).toEqual([0, 3]);
    expect(ctx.profiles.map((p) => p.profile_id)).toEqual(["OWNER"]);
    expect(ctx.rotations[0].rotation_id).toBe("R_SOY_COVER");
    expect(ctx.strips.strips.R_SOY_COVER).toHaveLength(24); // strips still come from the fixture
    expect(ctx.assumptions["A-ACT-06"]).toEqual({ description: "Rangos de sliders", source: "AFA", status: "PENDING_AFA" });
    expect(ctx.assumptions["A-AGR-01"]).toBeDefined(); // fixture texts kept for ids the API did not send
    expect(fetch.mock.calls.map((c) => String(c[0]))).toEqual([
      `${BASE}/api/v1/actors/profiles`,
      `${BASE}/api/v1/rotations/catalog`,
      `${BASE}/api/v1/assumptions`,
      `${BASE}/api/v1/water-panel`,
    ]);
  });

  it("reads the precomputed search and returns null when it is missing", async () => {
    const searchBody = { profile_id: "OWNER", year_class_filter: "DRY", ranking: [] };
    const fetch = vi.fn(async (url: RequestInfo | URL) =>
      String(url).includes("actor=OWNER")
        ? json(searchBody)
        : json({ code: "SEARCH_NOT_PRECOMPUTED", message: "x", details: null }, 404),
    );
    const src = new ApiDataSource(BASE, new FixtureDataSource(), { fetch });
    expect(await src.search("OWNER", "DRY")).toEqual(searchBody);
    expect(String(fetch.mock.calls[0][0])).toBe(`${BASE}/api/v1/rotations/search?actor=OWNER&year_class_filter=DRY`);
    expect(await src.search("BANK", "ALL")).toBeNull();
  });

  it("posts the lite body and maps the response, taking the hash from X-Input-Hash", async () => {
    const fetch = vi.fn(async () => json(evalBody("body-hash"), 200, { "X-Input-Hash": "header-hash" }));
    const src = new ApiDataSource(BASE, new FixtureDataSource(), { fetch });
    const ev = await src.evaluate({
      plotId: PLOT,
      profileId: "BANK",
      overrides: { risk_aversion: 1.5 },
      yearClassFilter: "DRY",
      displayPreferences: ["WATER_SAFE_FIRST"],
    });
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${BASE}/api/v1/evaluate`);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      actor: "BANK",
      overrides: { risk_aversion: 1.5 },
      year_class_filter: "DRY",
      display_preferences: ["WATER_SAFE_FIRST"],
    });
    expect(ev).toMatchObject({ origin: "api", inputHash: "header-hash", displayOrder: ["R_MAIZE_SOY", "R_SOY_MONO"] });
    expect(ev.rotationNames.R_SOY_MONO).toBe("Soja continua");
  });

  it("omits defaults from the body (no overrides, all years, no preferences)", async () => {
    const fetch = vi.fn(async () => json(evalBody("h")));
    const src = new ApiDataSource(BASE, new FixtureDataSource(), { fetch });
    await src.evaluate({ plotId: PLOT, profileId: "OWNER", overrides: {}, yearClassFilter: "ALL", displayPreferences: [] });
    const init = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(JSON.parse(init[1].body as string)).toEqual({ actor: "OWNER" });
  });

  it("falls back to the fixtures when the API does not answer, and stays there", async () => {
    const fetch = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });
    const src = new ApiDataSource(BASE, new FixtureDataSource(), { fetch });
    const ctx = await src.getContext(PLOT);
    expect(ctx.origin).toBe("fixture");
    expect(src.isOffline).toBe(true);
    const calls = fetch.mock.calls.length;
    const ev = await src.evaluate({ plotId: PLOT, profileId: "TENANT" });
    expect(ev.origin).toBe("fixture");
    expect(ev.output.results[0].rotation_id).toBe("R_SOY_MONO"); // the tenant fixture
    expect(fetch.mock.calls.length).toBe(calls); // no more attempts once offline
  });

  it("falls back on a 5xx from /evaluate", async () => {
    const fetch = vi.fn(async () => json({ code: "DATA_UNAVAILABLE", message: "x", details: null }, 503));
    const src = new ApiDataSource(BASE, new FixtureDataSource(), { fetch });
    const ev = await src.evaluate({ plotId: PLOT, profileId: "OWNER" });
    expect(ev.origin).toBe("fixture");
  });

  it("falls back on a timeout", async () => {
    const fetch = vi.fn(
      (_url: RequestInfo | URL, init?: RequestInit) =>
        new Promise<Response>((_res, rej) => init?.signal?.addEventListener("abort", () => rej(init.signal!.reason))),
    );
    const src = new ApiDataSource(BASE, new FixtureDataSource(), { fetch, timeoutMs: 20 });
    const ev = await src.evaluate({ plotId: PLOT, profileId: "OWNER" });
    expect(ev.origin).toBe("fixture");
  });

  it("raises the typed error on a 4xx instead of hiding it behind fixtures", async () => {
    const fetch = vi.fn(async () => json({ code: "UNKNOWN_ACTOR", message: "actor 'X' desconocido", details: { allowed: ["OWNER"] } }, 422));
    const src = new ApiDataSource(BASE, new FixtureDataSource(), { fetch });
    const err = await src.evaluate({ plotId: PLOT, profileId: "OWNER" }).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 422, code: "UNKNOWN_ACTOR", details: { allowed: ["OWNER"] } });
    expect(src.isOffline).toBe(false);
  });

  it("discards an older response that arrives after a newer one", async () => {
    const first = deferred<Response>();
    const second = deferred<Response>();
    const queue = [first, second];
    const signals: AbortSignal[] = [];
    // The mock ignores the abort signal on purpose: the guard must not rely on fetch honoring it.
    const fetch = vi.fn((_url: RequestInfo | URL, init?: RequestInit) => {
      signals.push(init!.signal!);
      return queue.shift()!.promise;
    });
    const src = new ApiDataSource(BASE, new FixtureDataSource(), { fetch });
    const older = src.evaluate({ plotId: PLOT, profileId: "OWNER", overrides: { risk_aversion: 0.5 } });
    const newer = src.evaluate({ plotId: PLOT, profileId: "OWNER", overrides: { risk_aversion: 1 } });
    expect(signals[0].aborted).toBe(true); // the older request was cancelled
    second.resolve(json(evalBody("new")));
    first.resolve(json(evalBody("old")));
    await expect(newer).resolves.toMatchObject({ inputHash: "new" });
    await expect(older).rejects.toBeInstanceOf(StaleResponseError);
    expect(src.isOffline).toBe(false);
  });
});
