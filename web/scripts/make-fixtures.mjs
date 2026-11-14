// Authors the EXAMPLE engine outputs used by the web while the API does not exist.
// Every number here is an example chosen by hand for the demo layout: none of them is
// a result of the engine. The generated JSON files must validate against
// schemas/engine_output.schema.json (checked by src/fixtures/fixtures.test.ts).
//
// Run: node scripts/make-fixtures.mjs
import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const out = resolve(here, "../src/fixtures");

const EXAMPLE = "valor de ejemplo del fixture web, no es salida del motor";
const der = (method, ...from) => ({ kind: "DERIVED", method: `${method} (${EXAMPLE})`, derived_from: from });
const sup = (id) => ({ kind: "ASSUMPTION", assumption_id: id });
const pv = (value, unit, provenance) => ({ value, unit, provenance });
const obs = (dataset, variable, period, spatial, temporal, isModeled, note = null) => ({
  kind: "OBSERVED",
  source: {
    dataset,
    variable,
    period,
    spatial_resolution: spatial,
    temporal_resolution: temporal,
    is_modeled: isModeled,
    location_note: note,
  },
});

const POWER_PERIOD = { start: "1981-07-01", end: "2026-06-30" };
const SMAP_PERIOD = { start: "2026-11-01", end: "2026-11-10" };
const GRACE_PERIOD = { start: "2026-08-01", end: "2026-08-31" };
const NDVI_PERIOD = { start: "2001-01-01", end: "2025-12-31" };
const TOTAL_YEARS = 45;

// Strip months start in June (campaign year Jun..May). Index i -> calendar month (5 + i) % 12.
// Calendar cells follow A-AGR-01 (example dates, pending AFA); the web only draws them.
const DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
const calendarDays = (strip) => {
  const campaigns = strip.length / 12;
  const days = new Array(12).fill(0);
  strip.forEach((crop, i) => {
    const m = (5 + i) % 12;
    if (crop === null) days[m] += DAYS[m] / campaigns;
  });
  return days.map((d) => Math.round(d * 10) / 10);
};

const _ = null;
const S1 = "SOY_1ST", S2 = "SOY_2ND", ME = "MAIZE_EARLY", W = "WHEAT", V = "COVER_VETCH";
export const STRIPS = {
  R_SOY_MONO: [_, _, _, _, _, S1, S1, S1, S1, S1, S1, _, _, _, _, _, _, S1, S1, S1, S1, S1, S1, _],
  R_MAIZE_SOY: [_, _, _, _, ME, ME, ME, ME, ME, ME, _, _, _, _, _, _, _, S1, S1, S1, S1, S1, S1, _],
  R_WHEAT_SOY2_MAIZE: [W, W, W, W, W, W, S2, S2, S2, S2, S2, _, _, _, _, _, ME, ME, ME, ME, ME, ME, _, _],
  R_MAIZE_SOY_COVER: [_, _, _, _, ME, ME, ME, ME, ME, ME, _, V, V, V, V, V, _, S1, S1, S1, S1, S1, S1, _],
};

const months12 = (entries) => {
  const a = new Array(12).fill(0);
  for (const [m, f] of Object.entries(entries)) a[Number(m) - 1] = f;
  return a;
};
const vuln = (crop, event, entries, ref) => ({
  crop,
  event,
  frequency_by_month: months12(entries),
  provenance: der(`frecuencia de años históricos con el evento por mes (${ref})`, "NASA_POWER.T2M_MIN", "NASA_POWER.PRECTOTCORR"),
});

const rainEvidence = {
  dataset: "NASA_POWER",
  variable: "PRECTOTCORR",
  period: POWER_PERIOD,
  value: pv(412, "mm", obs("NASA_POWER", "PRECTOTCORR", POWER_PERIOD, "0.5° x 0.625°", "diaria", true, "celda que contiene el lote demo")),
  interpretation: `Mediana de lluvia de noviembre a marzo en 45 campañas; los años secos son el tercio con menos lluvia (${EXAMPLE}).`,
};
const smapEvidence = {
  dataset: "SMAP_L4",
  variable: "sm_rootzone",
  period: SMAP_PERIOD,
  value: pv(0.27, "m3/m3", obs("SMAP_L4", "sm_rootzone", SMAP_PERIOD, "~9 km", "3-horaria", true, "celda EASE-Grid de ~9 km")),
  interpretation: `Humedad de la zona de raíces al inicio del balance; describe la celda, no mide el lote (${EXAMPLE}).`,
};

const marginRanges = (dry, normal, wet) =>
  [
    ["DRY", dry],
    ["NORMAL", normal],
    ["WET", wet],
  ].map(([cls, [min, exp, max]]) => ({
    year_class: cls,
    minimum: pv(min, "USD/ha", der("margen bruto mínimo de la clase", "A-DEMO-02", "A-DEMO-06")),
    expected: pv(exp, "USD/ha", der("margen bruto ponderado de la clase", "A-DEMO-02", "A-DEMO-06")),
    maximum: pv(max, "USD/ha", der("margen bruto máximo de la clase", "A-DEMO-02", "A-DEMO-06")),
  }));

// Per-rotation example data that does not depend on the actor.
const ROTATIONS = {
  R_SOY_MONO: {
    is_current: true,
    water: "FEASIBLE",
    soil: -9,
    lossYears: [1988, 2008, 2017],
    worst: [2008, -142],
    rainBare: 286,
    riskBase: 60,
    ranges: marginRanges([-142, 96, 210], [180, 318, 402], [260, 371, 455]),
    vulnerability: [vuln(S1, "WATER_DEFICIT", { 1: 0.22, 2: 0.18 }, "A-WAT-04")],
    evidence: [
      rainEvidence,
      smapEvidence,
      {
        dataset: "MODIS_NDVI",
        variable: "NDVI",
        period: NDVI_PERIOD,
        value: pv(0.58, "fraction", obs("MODIS_NDVI", "NDVI 16 días", NDVI_PERIOD, "250 m", "16 días", false, "píxeles dentro del contorno del lote")),
        interpretation: `Fracción de meses de mayo a octubre con NDVI bajo el umbral de suelo cubierto (A-SOIL-10): el lote pasa el invierno descubierto (${EXAMPLE}).`,
      },
    ],
    benefits: [{ description: "Es la rotación que el productor ya conoce: menor capital de trabajo y logística simple (texto de ejemplo)." }],
    missing: [
      {
        item: "Profundidad de napa",
        why_it_matters: "Una napa a menos de 2 m puede aportar agua en años secos y cambiar la factibilidad (texto de ejemplo).",
        how_to_get: "Freatímetro en el lote o registro del productor.",
      },
    ],
    risks: [
      { risk_type: "SOIL", severity: "HIGH", description: "Siete meses por año con suelo desnudo: erosión y pérdida de carbono (texto de ejemplo).", basis: "EVIDENCE", reference: "NDVI" },
      { risk_type: "WEEDS", severity: "MEDIUM", description: "Barbecho largo favorece malezas resistentes (texto de ejemplo).", basis: "ASSUMPTION", reference: "A-SOIL-08" },
    ],
  },
  R_MAIZE_SOY: {
    is_current: false,
    water: "FEASIBLE",
    soil: 11,
    lossYears: [1988, 2008, 2017, 2022],
    worst: [2008, -188],
    rainBare: 241,
    riskBase: 50,
    ranges: marginRanges([-188, 120, 260], [230, 412, 520], [330, 468, 590]),
    vulnerability: [
      vuln(ME, "WATER_DEFICIT", { 12: 0.2, 1: 0.27 }, "A-WAT-04"),
      vuln(S1, "WATER_DEFICIT", { 1: 0.22, 2: 0.18 }, "A-WAT-04"),
    ],
    evidence: [rainEvidence, smapEvidence],
    benefits: [
      { description: "El rastrojo de maíz cubre el suelo y aporta carbono (texto de ejemplo).", value: pv(11, "index", der("índice ΔSuelo", "A-SOIL-01", "A-SOIL-04")) },
    ],
    missing: [],
    risks: [{ risk_type: "ECONOMIC", severity: "MEDIUM", description: "Mayor costo directo del maíz en años secos (texto de ejemplo).", basis: "ASSUMPTION", reference: "A-DEMO-04" }],
  },
  R_WHEAT_SOY2_MAIZE: {
    is_current: false,
    water: "RISKY",
    soil: 18,
    lossYears: [1988, 1995, 2008, 2009, 2011, 2017, 2022],
    worst: [2008, -236],
    rainBare: 132,
    riskBase: 90,
    ranges: marginRanges([-236, 88, 240], [250, 431, 560], [360, 502, 640]),
    vulnerability: [
      vuln(W, "FROST", { 7: 0.31, 8: 0.2 }, "A-CLI-05"),
      vuln(S2, "WATER_DEFICIT", { 1: 0.4, 2: 0.29 }, "A-WAT-04"),
      vuln(ME, "WATER_DEFICIT", { 12: 0.2, 1: 0.27 }, "A-WAT-04"),
    ],
    evidence: [
      rainEvidence,
      smapEvidence,
      {
        dataset: "NASA_POWER",
        variable: "T2M_MIN",
        period: POWER_PERIOD,
        value: pv(14, "count", obs("NASA_POWER", "T2M_MIN", POWER_PERIOD, "0.5° x 0.625°", "diaria", true)),
        interpretation: `Campañas con helada en julio durante el macollaje del trigo, según el umbral A-CLI-05 (${EXAMPLE}).`,
      },
    ],
    benefits: [{ description: "Tres cultivos en dos años: más ingreso y menos meses de suelo desnudo (texto de ejemplo)." }],
    missing: [],
    risks: [
      { risk_type: "WATER", severity: "HIGH", description: "En años secos el trigo deja el perfil con poca agua para la soja de segunda (texto de ejemplo).", basis: "ASSUMPTION", reference: "A-WAT-08" },
      { risk_type: "FROST", severity: "MEDIUM", description: "Heladas de julio y agosto sobre el trigo (texto de ejemplo).", basis: "EVIDENCE", reference: "T2M_MIN" },
    ],
  },
  R_MAIZE_SOY_COVER: {
    is_current: false,
    water: "UNKNOWN",
    soil: 24,
    lossYears: [1988, 2008, 2009, 2017, 2022],
    worst: [2008, -205],
    rainBare: 98,
    riskBase: 70,
    ranges: marginRanges([-205, 104, 250], [240, 446, 548], [340, 489, 610]),
    vulnerability: [
      vuln(ME, "WATER_DEFICIT", { 12: 0.2, 1: 0.27 }, "A-WAT-04"),
      vuln(S1, "WATER_DEFICIT", { 1: 0.27, 2: 0.2 }, "A-WAT-04"),
    ],
    evidence: [
      rainEvidence,
      smapEvidence,
      {
        dataset: "GRACE_FO",
        variable: "lwe_thickness",
        period: GRACE_PERIOD,
        value: pv(-38, "mm", obs("GRACE_FO", "lwe_thickness", GRACE_PERIOD, "~300 km", "mensual", true, "mascon regional")),
        interpretation: `Anomalía regional de agua total: contexto de déficit, no decide sola (A-WAT-10) (${EXAMPLE}).`,
      },
    ],
    benefits: [
      { description: "La vicia cubre el invierno, fija nitrógeno y frena malezas (texto de ejemplo).", value: pv(24, "index", der("índice ΔSuelo", "A-SOIL-01", "A-SOIL-06")) },
    ],
    missing: [
      {
        item: "Profundidad de napa",
        why_it_matters: "Sin napa no se sabe si la vicia deja agua suficiente para la soja: la factibilidad queda Desconocida (texto de ejemplo).",
        how_to_get: "Freatímetro en el lote o registro del productor.",
      },
    ],
    risks: [{ risk_type: "WATER", severity: "MEDIUM", description: "El consumo de agua del cultivo de servicio depende de la fecha de secado (texto de ejemplo).", basis: "ASSUMPTION", reference: "A-WAT-09" }],
  },
};

// Per-actor example scores (USD/ha). α in USD/ha/point and λ as ratio match demo_context.json.
const ACTORS = {
  OWNER: { alpha: 6, lambda: 0.5, totals: { R_MAIZE_SOY_COVER: 446, R_WHEAT_SOY2_MAIZE: 431, R_MAIZE_SOY: 412, R_SOY_MONO: 318 } },
  TENANT: { alpha: 0.5, lambda: 0.2, totals: { R_SOY_MONO: 302, R_WHEAT_SOY2_MAIZE: 296, R_MAIZE_SOY: 281, R_MAIZE_SOY_COVER: 240 } },
  COOP: { alpha: 5, lambda: 0.5, totals: { R_MAIZE_SOY_COVER: 452, R_MAIZE_SOY: 420, R_WHEAT_SOY2_MAIZE: 405, R_SOY_MONO: 310 } },
  BANK: { alpha: 1.5, lambda: 1, totals: { R_MAIZE_SOY: 355, R_SOY_MONO: 349, R_MAIZE_SOY_COVER: 331, R_WHEAT_SOY2_MAIZE: 298 } },
};

const round2 = (x) => Math.round(x * 100) / 100;

function buildOutput(actorId) {
  const actor = ACTORS[actorId];
  const order = Object.entries(actor.totals).sort((a, b) => b[1] - a[1]);
  const currentTotal = actor.totals.R_SOY_MONO;
  const results = order.map(([id, total], i) => {
    const r = ROTATIONS[id];
    const soilTerm = round2(actor.alpha * r.soil);
    const riskTerm = round2(actor.lambda * r.riskBase);
    const npv = round2(total - soilTerm + riskTerm);
    return {
      rotation_id: id,
      rank: i + 1,
      is_current: r.is_current,
      eligible: true,
      exclusion_reasons: [],
      breakdown: {
        npv: pv(npv, "USD/ha", der("VAN de márgenes esperados en el horizonte del actor", "A-DEMO-02", "A-DEMO-04", "A-DEMO-06", "NASA_POWER.PRECTOTCORR")),
        soil_term: pv(soilTerm, "USD/ha", der("α · ΔSuelo", "A-ACT-01", "A-SOIL-01")),
        risk_term: pv(riskTerm, "USD/ha", der("λ · expected shortfall de márgenes", "A-ACT-05")),
        total: pv(total, "USD/ha", der("VAN + α·ΔSuelo − λ·Riesgo", "npv", "soil_term", "risk_term")),
      },
      soil_delta_index: pv(r.soil, "index", der("índice ΔSuelo de 5 componentes", "A-SOIL-01", "A-SOIL-02", "A-SOIL-04", "A-SOIL-06")),
      water_feasibility: r.water,
      water_adjustments: [],
      score_delta_vs_current: pv(total - currentTotal, "USD/ha", der("diferencia de puntaje contra la rotación actual", "total")),
      margin_ranges: r.ranges,
      loss_years: { count: r.lossYears.length, total: TOTAL_YEARS, years: r.lossYears },
      worst_year_margin: pv(r.worst[1], "USD/ha", der("margen bruto del peor año del registro", "A-DEMO-02", "A-DEMO-06")),
      worst_year: r.worst[0],
      rain_on_bare_soil: pv(r.rainBare, "mm", der("lluvia mediana caída en meses con suelo desnudo", "NASA_POWER.PRECTOTCORR", "A-AGR-01")),
      bare_soil_calendar: { days_by_month: calendarDays(STRIPS[id]), provenance: der("días sin cultivo vivo por mes según el calendario", "A-AGR-01", "A-SOIL-02") },
      vulnerability_calendar: r.vulnerability,
      evidence: r.evidence,
      benefits: r.benefits,
      missing: r.missing,
      risks: r.risks,
    };
  });
  return {
    engine_version: "fixture-web-0.1.0 (ejemplo)",
    // Valid SHA-256 shape, but of a fixed label, not of a real EngineInput.
    input_hash: createHash("sha256").update(`rastrojo-web-example-${actorId}`).digest("hex"),
    results,
  };
}

for (const actorId of Object.keys(ACTORS)) {
  const json = JSON.stringify(buildOutput(actorId), null, 2) + "\n";
  await writeFile(resolve(out, `engine_output.${actorId.toLowerCase()}.json`), json);
  if (actorId === "OWNER") await writeFile(resolve(out, "engine_output.demo.json"), json);
}
await writeFile(resolve(out, "rotation_strips.json"), JSON.stringify({ start_month: 6, calendar_assumption_id: "A-AGR-01", strips: STRIPS }, null, 2) + "\n");
console.log("fixtures written to src/fixtures");
