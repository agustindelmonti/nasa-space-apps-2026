import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { AgentClient, AgentUnavailable } from "./AgentClient";
import { ApiError } from "./ApiDataSource";
import { richText } from "../lib/richText";

const BASE = "http://api.test";
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

const reply = {
  text: "1. Maíz / Soja: 1.353 USD/ha",
  intent: "ranking",
  trace: [{ tool: "evaluate_rotations", params: { actor: "OWNER" }, input_hash: "abc", engine_version: "0.1.0" }],
  state: { actor: "OWNER", current_rotation_id: "R_SOY_MONO", pending_profile: null, horizon_override: null },
  suggestions: ["¿Por qué sale primera?"],
  mode: "scripted",
};

describe("AgentClient", () => {
  it("posts the question and the stored state to /ask", async () => {
    const fetch = vi.fn(async () => json(reply));
    const client = new AgentClient(BASE, { fetch });
    const state = { actor: "BANK", current_rotation_id: "R_SOY_MONO" };
    const res = await client.send("¿Cuál me conviene?", state, "web");
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${BASE}/api/v1/ask`);
    expect(JSON.parse(init.body as string)).toEqual({ text: "¿Cuál me conviene?", channel: "web", state });
    expect(res.trace[0].tool).toBe("evaluate_rotations");
    expect(res.mode).toBe("scripted");
  });

  it("talks to the same origin when the base is \"/\" (web and API on one domain)", async () => {
    const fetch = vi.fn(async () => json(reply));
    const client = new AgentClient("/", { fetch });
    expect(client.available).toBe(true);
    await client.send("¿Cuándo queda el suelo desnudo?", null, "web");
    const [url] = fetch.mock.calls[0] as unknown as [string];
    expect(url).toBe("/api/v1/ask");
  });

  it("uses /chat/simulate for the WhatsApp simulator and returns the split messages", async () => {
    const fetch = vi.fn(async () => json({ ...reply, messages: ["primera parte", "segunda parte"] }));
    const client = new AgentClient(BASE, { fetch });
    const res = await client.send("hola", null, "whatsapp");
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${BASE}/api/v1/chat/simulate`);
    expect(JSON.parse(init.body as string)).toEqual({ text: "hola", channel: "whatsapp" });
    expect(res.messages).toEqual(["primera parte", "segunda parte"]);
  });

  it("says it needs the engine when the API does not answer or is not configured", async () => {
    const down = new AgentClient(BASE, {
      fetch: vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    });
    await expect(down.send("hola", null, "web")).rejects.toBeInstanceOf(AgentUnavailable);
    await expect(new AgentClient(undefined).send("hola", null, "web")).rejects.toBeInstanceOf(AgentUnavailable);
  });

  it("raises the typed error on a 4xx", async () => {
    const client = new AgentClient(BASE, { fetch: vi.fn(async () => json({ code: "VALIDATION_ERROR", message: "la solicitud no es válida", details: [] }, 422)) });
    const err = await client.send("x", null, "web").catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("VALIDATION_ERROR");
  });
});

describe("richText", () => {
  it("turns the template bold marks into <strong> and keeps line breaks", () => {
    const html = renderToStaticMarkup(richText("## Título\n**Por qué** sale *primera*\n- 1.353 USD/ha"));
    expect(html).toBe("Título<br/><strong>Por qué</strong> sale <strong>primera</strong><br/>- 1.353 USD/ha");
  });
});
