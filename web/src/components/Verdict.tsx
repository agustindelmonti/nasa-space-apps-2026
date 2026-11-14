import { useEffect, useState, type ReactNode } from "react";
import { CircleCheck, CircleX, Handshake, TriangleAlert } from "lucide-react";
import type { RotationResult, SowingDecision } from "../data/types";
import { orderRows } from "../lib/rankDiff";
import { formatNumber, formatSigned } from "../lib/format";
import { ProvenanceBadge } from "./ProvenanceBadge";
import { WaterState } from "./WaterState";

interface Props {
  results: RotationResult[];
  order: string[];
  names: Record<string, string>;
  actorLabel: string;
  isTenant: boolean;
  sowing?: SowingDecision;
  /** Rent the user typed (qq/ha); undefined = the assumption A-ECO-05. */
  rentQq?: number;
  onRentQq: (qq: number | undefined) => void;
  rentDisabled?: boolean;
  /** The actor selector: changing who decides is the main move. */
  children: ReactNode;
}

const VERDICT = {
  SOW: { Icon: CircleCheck, cls: "v-sow" },
  SOW_WITH_RISK: { Icon: TriangleAlert, cls: "v-risk" },
  RENT_BETTER: { Icon: Handshake, cls: "v-rent" },
  DONT_SOW: { Icon: CircleX, cls: "v-no" },
} as const;

/** Wraps the rotation name inside the API's headline so it stands out; the text itself is the API's. */
function emphasize(text: string, name: string | undefined) {
  if (!name || !text.includes(name)) return text;
  const [a, ...rest] = text.split(name);
  return (
    <>
      {a}
      <em>{name}</em>
      {rest.join(name)}
    </>
  );
}

function Stat({ label, children, note }: { label: string; children: ReactNode; note?: ReactNode }) {
  return (
    <div className="stat">
      <dt>{label}</dt>
      <dd>
        <span className="stat-value">{children}</span>
        {note && <span className="stat-note">{note}</span>}
      </dd>
    </div>
  );
}

/** The answer first. "¿Me conviene sembrar?" (or, for a tenant, "¿sigo arrendando?") as the API decides
 *  it, with its figures as stat tiles. Only restates figures that come from the API. */
export function Verdict({ results, order, names, actorLabel, isTenant, sowing, rentQq, onRentQq, rentDisabled, children }: Props) {
  const rows = orderRows(results, order);
  const top = rows.find((r) => r.eligible) ?? null;
  const current = results.find((r) => r.is_current) ?? null;
  const name = (r: RotationResult) => names[r.rotation_id] ?? r.rotation_id;
  const delta = top && !top.is_current ? top.score_delta_vs_current : null;
  const [draft, setDraft] = useState<string>("");
  const shownRent = sowing ? formatNumber(sowing.rent_qq, 1) : "";
  useEffect(() => setDraft(rentQq === undefined ? shownRent : formatNumber(rentQq, 1)), [rentQq, shownRent]);
  const v = sowing ? VERDICT[sowing.verdict] : null;
  const alt = isTenant ? "devolver el campo" : "alquilar";

  const commit = () => {
    const n = Number(draft.replace(",", "."));
    if (draft.trim() === "" || !Number.isFinite(n) || n < 0 || n > 60) {
      setDraft(rentQq === undefined ? shownRent : formatNumber(rentQq, 1));
      return;
    }
    if (rentQq === undefined && sowing && Math.abs(n - sowing.rent_qq) < 1e-9) return;
    onRentQq(n);
  };

  return (
    <section className={`verdict${v ? ` ${v.cls}` : ""}`} aria-labelledby="h-verdict">
      <div className="verdict-bar">
        {children}
        {sowing && (
          <label className="rent">
            <span className="label">{isTenant ? "Arriendo que pagás" : "Arriendo que te pagarían"}</span>
            <span className="rent-field">
              <input
                type="text"
                inputMode="decimal"
                value={draft}
                disabled={rentDisabled}
                aria-describedby="rent-help"
                onChange={(e) => setDraft(e.target.value)}
                onBlur={commit}
                onKeyDown={(e) => e.key === "Enter" && (e.currentTarget as HTMLInputElement).blur()}
              />
              <span className="unit">qq soja/ha</span>
              {rentQq === undefined ? (
                <ProvenanceBadge provenance={{ kind: "ASSUMPTION", assumption_id: "A-ECO-05" }} />
              ) : (
                <button type="button" className="btn-secondary btn-sm" onClick={() => onRentQq(undefined)}>
                  Usar el de referencia
                </button>
              )}
            </span>
            <span id="rent-help" className="sr-only">
              Cambiá el arriendo y el motor vuelve a decidir si conviene sembrar.
            </span>
          </label>
        )}
      </div>

      <div className="verdict-body" aria-live="polite">
        <p className="label verdict-q">{isTenant ? "¿Me conviene seguir arrendando?" : "¿Me conviene sembrar?"}</p>
        {sowing && v ? (
          <>
          <h2 id="h-verdict" className="verdict-line" data-verdict={sowing.verdict}>
            <v.Icon className="verdict-icon" size={34} strokeWidth={1.75} aria-hidden="true" />
            <span>{sowing.headline}</span>
          </h2>
          {sowing.detail && (
            <p className="verdict-detail">{emphasize(sowing.detail, sowing.rotation_id ? names[sowing.rotation_id] : undefined)}</p>
          )}
          </>
        ) : (
          <h2 id="h-verdict" className="verdict-line">
            {top ? (
              <span>
                Para el {actorLabel.toLowerCase()}, la mejor opción es <em>{name(top)}</em>.
              </span>
            ) : (
              <span>Para el {actorLabel.toLowerCase()} ninguna rotación es elegible con estas restricciones.</span>
            )}
          </h2>
        )}
      </div>

      {sowing && sowing.vs_rent && sowing.vs_fallow && (
        <dl className="stats">
          <Stat label={`Diferencia con ${alt}`} note="USD/ha por año">
            <span className={sowing.vs_rent.value >= 0 ? "pos-val" : "neg-val"}>{formatSigned(sowing.vs_rent.value)}</span>
          </Stat>
          <Stat label="Diferencia con barbecho" note="USD/ha por año">
            <span className={sowing.vs_fallow.value >= 0 ? "pos-val" : "neg-val"}>{formatSigned(sowing.vs_fallow.value)}</span>
          </Stat>
          <Stat label={`Campañas peor que ${alt}`} note={`de ${sowing.campaigns_total}`}>
            {sowing.campaigns_below_rent}
          </Stat>
          {sowing.breakeven_rent_qq && (
            <Stat label="Arriendo de equilibrio" note="qq soja/ha">
              {formatNumber(sowing.breakeven_rent_qq.value, 1)}
            </Stat>
          )}
          {sowing.water && (
            <Stat label="Agua">
              <WaterState state={sowing.water} />
            </Stat>
          )}
        </dl>
      )}

      <p className="verdict-foot small soft">
        {top && (
          <>
            Mejor rotación para el {actorLabel.toLowerCase()}: <b>{name(top)}</b>
            {delta && current && (
              <>
                {" "}
                ({formatSigned(delta.value)} USD/ha de puntaje frente a {name(current)}, la actual)
              </>
            )}
            .{" "}
          </>
        )}
        {sowing?.expected_margin && (
          <>
            Margen esperado {formatNumber(sowing.expected_margin.value)} USD/ha contra un arriendo de {formatNumber(sowing.rent.value)} USD/ha.
          </>
        )}
      </p>
    </section>
  );
}
