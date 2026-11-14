import type { EvaluateRequest, Evaluation, PlotContext } from "./types";

/**
 * Everything the components read goes through this interface. It is backed by the API
 * (`ApiDataSource`) or by the example fixtures (`FixtureDataSource`, offline demo).
 * Implementations never compute scores: they return what the engine (or a fixture) says.
 */
export interface DataSource {
  /** What the source is configured to use; each result also says where it actually came from (`origin`). */
  readonly kind: "fixture" | "api";
  getContext(plotId: string, signal?: AbortSignal): Promise<PlotContext>;
  evaluate(request: EvaluateRequest, signal?: AbortSignal): Promise<Evaluation>;
}

/** Thrown when a newer evaluation superseded this one; callers ignore it. */
export class StaleResponseError extends Error {
  constructor() {
    super("respuesta descartada: hay un pedido más nuevo");
    this.name = "StaleResponseError";
  }
}

export const isIgnorable = (e: unknown) =>
  e instanceof StaleResponseError || (e instanceof Error && e.name === "AbortError");
