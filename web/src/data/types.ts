// Contract types come from the JSON Schemas (generated); this file only composes them.
import type { EngineOutput, PValue, RotationResult, WaterFeasibility, Crop } from "../types/generated/engine_output";
import type { ActorProfile, Plot, Rotation } from "../types/generated/engine_input";

export type { EngineOutput, PValue, RotationResult, WaterFeasibility, Crop, ActorProfile, Plot, Rotation };

export type ProfileId = "OWNER" | "TENANT" | "COOP" | "BANK";

export interface WaterCell {
  label: string;
  /** null when the dataset is not downloaded yet (the limitation says so). */
  value: PValue | null;
  limitation: string;
}

export interface AssumptionInfo {
  description: string;
  source: string;
  status: string;
}

/** Month cells of the campaign strip, as delivered by the catalog (A-AGR-01). */
export interface RotationStrips {
  /** Calendar month (1..12) of the first cell. */
  start_month: number;
  calendar_assumption_id: string;
  strips: Record<string, (Crop | null)[]>;
}

/** Where a piece of data came from: the real API or the example fixtures (offline demo). */
export type Origin = "api" | "fixture";

/** Slider ranges delivered by `GET /actors/profiles` (A-ACT-06). */
export interface SliderLimits {
  horizon_years: [number, number];
  alpha: [number, number];
  lambda: [number, number];
  discount_rate?: [number, number];
}

/** What the page needs besides the evaluation. Profiles, slider limits and catalog come from
 *  `/actors/profiles` and `/rotations/catalog` when the API answers; the rest is still a fixture. */
export interface PlotContext {
  origin: Origin;
  slider_limits: SliderLimits;
  plot: Plot;
  rotations: Rotation[];
  profiles: ActorProfile[];
  water_panel: { grace: WaterCell; smap: WaterCell; rain: WaterCell };
  assumptions: Record<string, AssumptionInfo>;
  strips: RotationStrips;
}

export type YearClassFilter = "ALL" | "DRY" | "NORMAL" | "WET";
export type DisplayPreference = "WATER_SAFE_FIRST" | "DOUBLE_CROP_FIRST";

/** Profile overrides sent as-is to `/evaluate` (`overrides` in the lite body). */
export interface ProfileOverrides {
  horizon_years?: number;
  alpha?: number;
  risk_aversion?: number;
}

export interface EvaluateRequest {
  plotId: string;
  profileId: ProfileId;
  overrides?: ProfileOverrides;
  yearClassFilter?: YearClassFilter;
  displayPreferences?: DisplayPreference[];
  currentRotationId?: string;
  /** Rent of the field in qq of soy/ha for "¿me conviene sembrar?" (default: assumption A-ECO-05). */
  rentQq?: number;
}

/** "¿Me conviene sembrar?" as the API decides it (`sowing` in `/evaluate`). */
export interface SowingDecision {
  verdict: "SOW" | "SOW_WITH_RISK" | "RENT_BETTER" | "DONT_SOW";
  actor: string;
  rotation_id: string | null;
  expected_margin: PValue | null;
  rent: PValue;
  rent_qq: number;
  fallow_cost: PValue;
  vs_rent: PValue | null;
  vs_fallow: PValue | null;
  breakeven_rent_qq: PValue | null;
  campaigns_below_rent: number;
  campaigns_below_fallow: number;
  campaigns_total: number;
  water: WaterFeasibility | null;
  headline: string;
  detail: string;
  reasons: string[];
  assumptions: string[];
}

/** Deterministic explanation templates rendered by the API (`explanation` in `/evaluate`). */
export interface RotationExplanation {
  rotation_id: string;
  title: string;
  /** The fixed five-section card, in order: Por qué, Evidencia, Beneficios, Qué falta saber, Riesgos. */
  sections: Record<string, string[]>;
  extras: Record<string, string[]>;
  closing: string;
}

export interface Explanation {
  input_hash: string;
  engine_version: string;
  templates_version: string;
  summary: string[];
  rotations: RotationExplanation[];
  disclaimers: string[];
  assumption_ids: string[];
}

/** One evaluation as the page consumes it: the engine output plus what the API adds around it. */
export interface Evaluation {
  /** Only from the API; the fixtures carry none. */
  explanation?: Explanation;
  /** Only from the API. */
  sowing?: SowingDecision;
  origin: Origin;
  output: EngineOutput;
  /** rotation_id -> display name, from the API response (not from a fixed context). */
  rotationNames: Record<string, string>;
  /** Order computed by the API from the display preferences (equals rank order without them). */
  displayOrder: string[];
  inputHash: string;
}

/** Numeric columns of the precomputed search; unit and provenance are declared once per column. */
export type SearchColumn = "score" | "expected_annual_margin" | "soil_delta_index" | "risk";

export interface SearchRow {
  rank: number;
  rotation_id: string;
  name: string;
  /** [winter, summer] crop codes per campaign ("" when empty). */
  campaigns: [string, string][];
  in_catalog: boolean;
  is_current: boolean;
  pareto: boolean;
  score: number;
  expected_annual_margin: number | null;
  soil_delta_index: number | null;
  risk: number | null;
  water_feasibility: WaterFeasibility | null;
}

/** `GET /rotations/search`: exhaustive search precomputed with the predefined profile. */
export interface RotationSearch {
  generator_version: string;
  engine_version: string;
  input_hash: string;
  profile_id: ProfileId;
  year_class_filter: YearClassFilter;
  rules: string[];
  counts: {
    valid_campaigns: number;
    generated: number;
    pruned_by_rule: Record<string, number>;
    kept_by_rules: number;
    evaluated: number;
    eligible: number;
    /** Eligible rotations left out because their water is not feasible or unknown. */
    water_excluded?: number;
    pareto: number;
  };
  best_found: string | null;
  best_catalog: string | null;
  gain_vs_catalog: PValue | null;
  columns: Record<SearchColumn, Pick<PValue, "unit" | "provenance">>;
  ranking: SearchRow[];
}
