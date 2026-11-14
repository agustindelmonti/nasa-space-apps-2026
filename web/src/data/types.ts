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

/** What the page needs besides the evaluation (future: /plots/{id}/context, /rotations/catalog, /actors/profiles, /assumptions). */
export interface PlotContext {
  plot: Plot;
  rotations: Rotation[];
  profiles: ActorProfile[];
  water_panel: { grace: WaterCell; smap: WaterCell; rain: WaterCell };
  assumptions: Record<string, AssumptionInfo>;
  strips: RotationStrips;
}

export interface EvaluateRequest {
  plotId: string;
  profileId: ProfileId;
}
