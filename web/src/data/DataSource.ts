import type { EngineOutput, EvaluateRequest, PlotContext } from "./types";

/**
 * Everything the components read goes through this interface. Today it is backed by
 * fixtures; the API client will implement the same contract without touching components.
 * Implementations never compute scores: they return what the engine (or a fixture) says.
 */
export interface DataSource {
  /** "fixture" shows the example-data notice in the UI. */
  readonly kind: "fixture" | "api";
  getContext(plotId: string): Promise<PlotContext>;
  evaluate(request: EvaluateRequest, signal?: AbortSignal): Promise<EngineOutput>;
}
