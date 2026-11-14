// Contract types come from the JSON Schemas (generated); this file only composes them.
import type { EngineOutput, PValue, RotationResult, WaterFeasibility, Crop } from "../types/generated/engine_output";
import type { ActorProfile, Plot, Rotation } from "../types/generated/engine_input";

export type { EngineOutput, PValue, RotationResult, WaterFeasibility, Crop, ActorProfile, Plot, Rotation };

export type ProfileId = "OWNER" | "TENANT" | "COOP" | "BANK";

export interface WaterCell {
  label: string;
  value: PValue;
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
  origin: Origin;
  output: EngineOutput;
  /** rotation_id -> display name, from the API response (not from a fixed context). */
  rotationNames: Record<string, string>;
  /** Order computed by the API from the display preferences (equals rank order without them). */
  displayOrder: string[];
  inputHash: string;
}
