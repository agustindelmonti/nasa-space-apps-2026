import type { DataSource } from "./DataSource";
import type { EngineOutput, EvaluateRequest, PlotContext, ProfileId } from "./types";
import context from "../fixtures/demo_context.json";
import strips from "../fixtures/rotation_strips.json";
import owner from "../fixtures/engine_output.owner.json";
import tenant from "../fixtures/engine_output.tenant.json";
import coop from "../fixtures/engine_output.coop.json";
import bank from "../fixtures/engine_output.bank.json";

const outputs: Record<ProfileId, unknown> = { OWNER: owner, TENANT: tenant, COOP: coop, BANK: bank };

/** Serves the example fixtures (validated against the schema in fixtures.test.ts). */
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

  async getContext(plotId: string): Promise<PlotContext> {
    if (plotId !== context.plot.plot_id) throw new Error(`Lote sin datos de ejemplo: ${plotId}`);
    const { note: _note, ...rest } = context;
    return this.wait({ ...rest, strips } as unknown as PlotContext);
  }

  async evaluate(request: EvaluateRequest, signal?: AbortSignal): Promise<EngineOutput> {
    const out = outputs[request.profileId];
    if (!out) throw new Error(`Actor sin datos de ejemplo: ${request.profileId}`);
    return this.wait(structuredClone(out) as EngineOutput, signal);
  }
}
