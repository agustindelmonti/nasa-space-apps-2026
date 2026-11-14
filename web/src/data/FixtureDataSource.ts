import type { DataSource } from "./DataSource";
import type { EngineOutput, EvaluateRequest, Evaluation, PlotContext, ProfileId, SliderLimits } from "./types";
import context from "../fixtures/demo_context.json";
import strips from "../fixtures/rotation_strips.json";
import owner from "../fixtures/engine_output.owner.json";
import tenant from "../fixtures/engine_output.tenant.json";
import coop from "../fixtures/engine_output.coop.json";
import bank from "../fixtures/engine_output.bank.json";

const outputs: Record<ProfileId, unknown> = { OWNER: owner, TENANT: tenant, COOP: coop, BANK: bank };

/** Same ranges as A-ACT-06 in the API registry; only used while the API is unreachable. */
export const FIXTURE_SLIDER_LIMITS: SliderLimits = { horizon_years: [1, 20], alpha: [0, 20], lambda: [0, 3] };

/** Serves the example fixtures (validated against the schema in fixtures.test.ts).
 *  It ignores overrides, year class and display preferences: it cannot evaluate anything. */
export class FixtureDataSource implements DataSource {
  readonly kind = "fixture" as const;

  constructor(private readonly latencyMs = 0) {}

  private wait<T>(value: T, signal?: AbortSignal): Promise<T> {
    if (!this.latencyMs) return Promise.resolve(value);
    return new Promise((res, rej) => {
      const t = setTimeout(() => res(value), this.latencyMs);
      signal?.addEventListener("abort", () => {
        clearTimeout(t);
        rej(new DOMException("aborted", "AbortError"));
      });
    });
  }

  async getContext(plotId: string, signal?: AbortSignal): Promise<PlotContext> {
    if (plotId !== context.plot.plot_id) throw new Error(`Lote sin datos de ejemplo: ${plotId}`);
    const { note: _note, ...rest } = context;
    const ctx = { ...rest, strips, origin: "fixture", slider_limits: FIXTURE_SLIDER_LIMITS };
    return this.wait(ctx as unknown as PlotContext, signal);
  }

  async evaluate(request: EvaluateRequest, signal?: AbortSignal): Promise<Evaluation> {
    const out = outputs[request.profileId] as EngineOutput | undefined;
    if (!out) throw new Error(`Actor sin datos de ejemplo: ${request.profileId}`);
    const output = structuredClone(out);
    return this.wait<Evaluation>(
      {
        origin: "fixture",
        output,
        rotationNames: Object.fromEntries(context.rotations.map((r) => [r.rotation_id, r.name])),
        displayOrder: [...output.results].sort((a, b) => a.rank - b.rank).map((r) => r.rotation_id),
        inputHash: output.input_hash,
      },
      signal,
    );
  }
}
