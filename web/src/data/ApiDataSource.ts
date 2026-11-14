import { StaleResponseError, type DataSource } from "./DataSource";
import type { ActorProfile, EngineOutput, EvaluateRequest, Evaluation, PlotContext, Rotation, SliderLimits } from "./types";

/** Typed error body of the API: `{code, message, details}`. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** The API did not answer (network down, timeout or a 5xx): the caller falls back to fixtures. */
class Unreachable extends Error {
  constructor(reason: string) {
    super(reason);
    this.name = "Unreachable";
  }
}

interface EvaluateResponse {
  input_hash: string;
  engine_version: string;
  engine_output: EngineOutput;
  rotation_names: Record<string, string>;
  display_order: string[];
}

interface Options {
  /** Injected for tests; defaults to the global fetch. */
  fetch?: typeof fetch;
  timeoutMs?: number;
}

/**
 * Talks to `/api/v1` (profiles, catalog and lite `/evaluate`). When the API does not answer it
 * switches, for the rest of the session, to the fallback source (the example fixtures) and
 * every result says so through `origin`. Only the latest evaluation resolves: an older one in
 * flight is aborted and, if its response still arrives, discarded with `StaleResponseError`.
 */
export class ApiDataSource implements DataSource {
  readonly kind = "api" as const;
  private offline = false;
  private latest: AbortController | null = null;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;

  constructor(
    private readonly baseUrl: string,
    private readonly fallback: DataSource,
    options: Options = {},
  ) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.fetchImpl = options.fetch ?? ((...args) => fetch(...args));
    this.timeoutMs = options.timeoutMs ?? 15_000;
  }

  /** True once the API failed to answer and the fixtures took over. */
  get isOffline() {
    return this.offline;
  }

  private async request<T>(path: string, init: RequestInit, signal?: AbortSignal): Promise<{ body: T; headers: Headers }> {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(new Unreachable("timeout")), this.timeoutMs);
    const onAbort = () => ctrl.abort(signal?.reason ?? new DOMException("aborted", "AbortError"));
    if (signal?.aborted) onAbort();
    signal?.addEventListener("abort", onAbort);
    try {
      let res: Response;
      try {
        res = await this.fetchImpl(`${this.baseUrl}/api/v1${path}`, { ...init, signal: ctrl.signal });
      } catch (e) {
        if (signal?.aborted) throw new DOMException("aborted", "AbortError");
        throw new Unreachable(e instanceof Error ? e.message : String(e));
      }
      if (res.status >= 500) throw new Unreachable(`HTTP ${res.status}`);
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        throw new ApiError(res.status, body?.code ?? "HTTP_ERROR", body?.message ?? `HTTP ${res.status}`, body?.details ?? null);
      }
      return { body: body as T, headers: res.headers };
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
    }
  }

  async getContext(plotId: string, signal?: AbortSignal): Promise<PlotContext> {
    const base = await this.fallback.getContext(plotId, signal);
    if (this.offline) return base;
    try {
      const [profiles, catalog] = await Promise.all([
        this.request<{ profiles: ActorProfile[]; slider_limits: SliderLimits }>("/actors/profiles", { method: "GET" }, signal),
        this.request<{ rotations: Rotation[] }>("/rotations/catalog", { method: "GET" }, signal),
      ]);
      return {
        ...base,
        origin: "api",
        profiles: profiles.body.profiles,
        slider_limits: profiles.body.slider_limits,
        rotations: catalog.body.rotations,
      };
    } catch (e) {
      if (!(e instanceof Unreachable)) throw e;
      this.offline = true;
      return base;
    }
  }

  async evaluate(request: EvaluateRequest, signal?: AbortSignal): Promise<Evaluation> {
    if (this.offline) return this.fallback.evaluate(request, signal);
    this.latest?.abort();
    const mine = new AbortController();
    this.latest = mine;
    const onAbort = () => mine.abort();
    signal?.addEventListener("abort", onAbort);

    const body: Record<string, unknown> = { actor: request.profileId };
    if (request.overrides && Object.keys(request.overrides).length) body.overrides = request.overrides;
    if (request.yearClassFilter && request.yearClassFilter !== "ALL") body.year_class_filter = request.yearClassFilter;
    if (request.displayPreferences?.length) body.display_preferences = request.displayPreferences;
    if (request.currentRotationId) body.current_rotation_id = request.currentRotationId;

    try {
      const { body: res, headers } = await this.request<EvaluateResponse>(
        "/evaluate",
        { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) },
        mine.signal,
      );
      if (this.latest !== mine) throw new StaleResponseError();
      return {
        origin: "api",
        output: res.engine_output,
        rotationNames: res.rotation_names,
        displayOrder: res.display_order,
        inputHash: headers.get("X-Input-Hash") ?? res.input_hash,
      };
    } catch (e) {
      if (this.latest !== mine) throw new StaleResponseError();
      if (!(e instanceof Unreachable)) throw e;
      this.offline = true;
      return this.fallback.evaluate(request, signal);
    } finally {
      signal?.removeEventListener("abort", onAbort);
      if (this.latest === mine) this.latest = null;
    }
  }
}
