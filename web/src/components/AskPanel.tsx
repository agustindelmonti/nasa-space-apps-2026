import { useEffect, useRef, useState, type FormEvent } from "react";
import { MessageCircle, Send, X } from "lucide-react";
import { AgentUnavailable, type AgentClient, type AskResponse, type Channel, type ConversationState } from "../data/AgentClient";
import { richText } from "../lib/richText";

interface Turn {
  id: number;
  role: "user" | "bot";
  text: string;
  /** WhatsApp simulator: the reply split as separate messages. */
  messages?: string[];
  trace?: AskResponse["trace"];
  error?: boolean;
}

interface Conversation {
  turns: Turn[];
  state: ConversationState | null;
  suggestions: string[];
  mode: AskResponse["mode"] | null;
}

const START_SUGGESTIONS = ["¿Cuál me conviene?", "¿Y si el año viene seco?", "¿Cuándo queda el suelo desnudo?"];
const empty = (): Conversation => ({ turns: [], state: null, suggestions: START_SUGGESTIONS, mode: null });
const MODE_LABEL = { scripted: "por reglas", llm: "con modelo de lenguaje" } as const;

interface Props {
  client: AgentClient;
  /** Actor chosen in the page; the first turn of each conversation starts from it. */
  actor: string;
  onClose: () => void;
}

let turnSeq = 0;

/** "Preguntale a Rastrojo": the web chat (`/ask`) and the WhatsApp simulator (`/chat/simulate`).
 *  It only shows what the API answers and keeps the `state` it hands back between turns. */
export function AskPanel({ client, actor, onClose }: Props) {
  const [channel, setChannel] = useState<Channel>("web");
  const [convs, setConvs] = useState<Record<Channel, Conversation>>({ web: empty(), whatsapp: empty() });
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const listRef = useRef<HTMLOListElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const conv = convs[channel];

  useEffect(() => {
    listRef.current?.lastElementChild?.scrollIntoView?.({ block: "end" });
  }, [conv.turns.length, busy]);

  useEffect(() => inputRef.current?.focus(), [channel]);

  const update = (ch: Channel, fn: (c: Conversation) => Conversation) => setConvs((all) => ({ ...all, [ch]: fn(all[ch]) }));

  async function ask(question: string) {
    const q = question.trim();
    if (!q || busy) return;
    const ch = channel;
    setText("");
    setBusy(true);
    update(ch, (c) => ({ ...c, suggestions: [], turns: [...c.turns, { id: ++turnSeq, role: "user", text: q }] }));
    const state = conv.state ?? { actor, current_rotation_id: "R_SOY_MONO" };
    try {
      const res = await client.send(q, state, ch);
      const messages = res.messages?.map((m) => m.trim()).filter(Boolean);
      update(ch, (c) => ({
        state: res.state,
        suggestions: res.suggestions,
        mode: res.mode,
        turns: [...c.turns, { id: ++turnSeq, role: "bot", text: res.text, messages, trace: res.trace }],
      }));
    } catch (e) {
      const msg = e instanceof AgentUnavailable ? e.message : `No pude responder: ${(e as Error).message}.`;
      update(ch, (c) => ({ ...c, suggestions: START_SUGGESTIONS, turns: [...c.turns, { id: ++turnSeq, role: "bot", text: msg, error: true }] }));
    } finally {
      setBusy(false);
    }
  }

  const submit = (e: FormEvent) => {
    e.preventDefault();
    void ask(text);
  };

  return (
    <aside className="ask" aria-labelledby="h-ask" data-channel={channel}>
      <div className="ask-head">
        <h2 id="h-ask" className="h-title">
          <MessageCircle size={20} strokeWidth={1.5} aria-hidden="true" />
          Preguntale a Rastrojo
        </h2>
        {conv.mode && (
          <span className="mode" data-mode={conv.mode}>
            {MODE_LABEL[conv.mode]}
          </span>
        )}
        <button type="button" className="icon-btn" aria-label="Cerrar el panel" onClick={onClose}>
          <X size={20} strokeWidth={1.5} aria-hidden="true" />
        </button>
      </div>
      <div className="seg seg-2" role="group" aria-label="Canal">
        <button type="button" aria-pressed={channel === "web"} onClick={() => setChannel("web")}>
          Rastrojo
        </button>
        <button type="button" aria-pressed={channel === "whatsapp"} onClick={() => setChannel("whatsapp")}>
          Simulador WhatsApp
        </button>
      </div>
      {channel === "whatsapp" && <p className="ask-note">Simulación: así llegaría la respuesta por WhatsApp, partida en mensajes.</p>}

      <ol ref={listRef} className="bubbles" aria-live="polite" aria-label="Conversación">
        {conv.turns.length === 0 && <li className="ask-empty">Preguntá en tus palabras sobre las rotaciones de tu lote.</li>}
        {conv.turns.map((t) =>
          t.role === "user" ? (
            <li key={t.id} className="bubble me">
              {t.text}
            </li>
          ) : (
            <li key={t.id} className={`bot-turn${t.error ? " is-error" : ""}`} data-role="bot">
              {(t.messages?.length ? t.messages : [t.text]).map((m, i) => (
                <p key={i} className="bubble bot">
                  {richText(m)}
                </p>
              ))}
              {t.trace && t.trace.length > 0 && (
                <details className="trace">
                  <summary>Cómo llegué a esto</summary>
                  <ol>
                    {t.trace.map((s, i) => (
                      <li key={i}>
                        <code className="tool">{s.tool}</code>
                        <span className="params">
                          {Object.entries(s.params)
                            .filter(([, v]) => v !== null && v !== undefined)
                            .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : String(v)}`)
                            .join(" · ") || "sin parámetros"}
                        </span>
                        {s.input_hash && (
                          <span className="hash" title={s.input_hash}>
                            hash {s.input_hash.slice(0, 12)} · motor {s.engine_version}
                          </span>
                        )}
                      </li>
                    ))}
                  </ol>
                </details>
              )}
            </li>
          ),
        )}
        {busy && (
          <li className="typing" aria-label="Rastrojo está escribiendo">
            <i />
            <i />
            <i />
          </li>
        )}
      </ol>

      {conv.suggestions.length > 0 && !busy && (
        <div className="suggest" role="group" aria-label="Sugerencias">
          {conv.suggestions.map((s) => (
            <button key={s} type="button" onClick={() => void ask(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <form className="ask-form" onSubmit={submit}>
        <label htmlFor="ask-input" className="sr-only">
          Tu pregunta
        </label>
        <input
          id="ask-input"
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Escribí tu pregunta"
          maxLength={1000}
          autoComplete="off"
        />
        <button type="submit" className="btn-primary" disabled={busy || !text.trim()}>
          <Send size={16} strokeWidth={1.5} aria-hidden="true" />
          Enviar
        </button>
      </form>
    </aside>
  );
}
