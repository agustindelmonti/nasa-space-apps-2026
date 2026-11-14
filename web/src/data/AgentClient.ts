import { ApiError } from "./ApiDataSource";

/** Conversation memory the API hands back on every turn (`state`); the page only stores it. */
export interface ConversationState {
  actor: string;
  current_rotation_id: string;
  pending_profile?: string | null;
  horizon_override?: number | null;
}

export interface ToolTrace {
  tool: string;
  params: Record<string, unknown>;
  input_hash?: string | null;
  engine_version?: string | null;
}

export interface AskResponse {
  text: string;
  intent: string;
  trace: ToolTrace[];
  state: ConversationState;
  suggestions: string[];
  mode: "scripted" | "llm";
  /** Only from `/chat/simulate`: the reply split as WhatsApp messages. */
  messages?: string[];
}

export type Channel = "web" | "whatsapp";

/** The agent cannot answer without the API (it runs the engine): no fixture fallback here. */
export class AgentUnavailable extends Error {
  constructor() {
    super("El asistente necesita conexión con el motor.");
    this.name = "AgentUnavailable";
  }
}

interface Options {
  fetch?: typeof fetch;
  timeoutMs?: number;
}

/** Client for `POST /ask` (web panel) and `POST /chat/simulate` (WhatsApp simulator). */
export class AgentClient {
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;
  private readonly baseUrl: string | null;

  constructor(baseUrl: string | null | undefined, options: Options = {}) {
    // "/" o "" = misma origen (API y web en el mismo dominio, por ejemplo en Vercel).
    this.baseUrl = baseUrl !== null && baseUrl !== undefined ? baseUrl.replace(/\/+$/, "") : null;
    this.fetchImpl = options.fetch ?? ((...args) => fetch(...args));
    this.timeoutMs = options.timeoutMs ?? 20_000;
  }

  get available() {
    return this.baseUrl !== null;
  }

  /** Sends one turn. `whatsapp` goes to `/chat/simulate` and returns the split `messages`. */
  async send(text: string, state: ConversationState | null, channel: Channel, signal?: AbortSignal): Promise<AskResponse> {
    if (!this.baseUrl) throw new AgentUnavailable();
    const path = channel === "whatsapp" ? "/chat/simulate" : "/ask";
    const body: Record<string, unknown> = { text, channel };
    if (state) body.state = state;
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), this.timeoutMs);
    const onAbort = () => ctrl.abort();
    signal?.addEventListener("abort", onAbort);
    let res: Response;
    try {
      res = await this.fetchImpl(`${this.baseUrl}/api/v1${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: ctrl.signal,
      });
    } catch (e) {
      if (signal?.aborted) throw e;
      throw new AgentUnavailable();
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
    }
    if (res.status >= 500) throw new AgentUnavailable();
    const json = await res.json().catch(() => null);
    if (!res.ok) throw new ApiError(res.status, json?.code ?? "HTTP_ERROR", json?.message ?? `HTTP ${res.status}`, json?.details ?? null);
    return json as AskResponse;
  }
}
