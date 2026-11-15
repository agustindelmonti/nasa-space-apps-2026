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
}

const VERDICT = {
  SOW: { Icon: CircleCheck, cls: "v-sow" },
  SOW_WITH_RISK: { Icon: TriangleAlert, cls: "v-risk" },
  RENT_BETTER: { Icon: Handshake, cls: "v-rent" },
  DONT_SOW: { Icon: CircleX, cls: "v-no" },
} as const;

/** Wraps the rotation name inside the API's sentence so it stands out; the text itself is the API's. */
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

/** The answer to "¿Me conviene sembrar?" (for a tenant, "¿sigo arrendando?") as the API decides it.
 *  It sits beside the ranking so changing who decides moves both in the same view.
 *  Only restates figures that come from the API. */
export function Verdict({ results, order, names, actorLabel, isTenant, sowing }: Props) {
  const rows = orderRows(results, order);
  const top = rows.find((r) => r.eligible) ?? null;
  const current = results.find((r) => r.is_current) ?? null;
  const name = (r: RotationResult) => names[r.rotation_id] ?? r.rotation_id;
  const delta = top && !top.is_current ? top.score_delta_vs_current : null;
  const v = sowing ? VERDICT[sowing.verdict] : null;
  const alt = isTenant ? "devolver el campo" : "alquilar";
  const question = isTenant ? "¿Me conviene seguir arrendando?" : "¿Me conviene sembrar?";

  return (
    <section className={`verdict${v ? ` ${v.cls}` : ""}`} aria-label={question}>
      <div className="verdict-body" aria-live="polite">
        {sowing && v ? (
          <>
            <h2 id="h-verdict" className="verdict-line" data-verdict={sowing.verdict}>
              <v.Icon className="verdict-icon" size={30} strokeWidth={1.75} aria-hidden="true" />
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

      {sowing && sowing.vs_rent && (
        <dl className="stats">
          <Stat label={`Frente a ${alt}`} note="USD/ha por año">
            <span className={sowing.vs_rent.value >= 0 ? "pos-val" : "neg-val"}>{formatSigned(sowing.vs_rent.value)}</span>
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
            <Stat label="Agua de esa rotación">
              <WaterState state={sowing.water} />
            </Stat>
          )}
        </dl>
      )}

      <p className="verdict-foot small soft">
        {sowing?.vs_fallow && (
          <>
            Frente a dejarlo en barbecho: <b>{formatSigned(sowing.vs_fallow.value)} USD/ha por año</b>.{" "}
          </>
        )}
        {top && delta && current && (
          <>
            {name(top)} suma {formatSigned(delta.value)} USD/ha de puntaje frente a {name(current)}, la actual.{" "}
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

interface RentProps {
  isTenant: boolean;
  sowing?: SowingDecision;
  /** Rent the user typed (qq/ha); undefined = the assumption A-ECO-05. */
  rentQq?: number;
  onRentQq: (qq: number | undefined) => void;
  disabled?: boolean;
}

/** The rent the verdict compares against. Editable: the engine decides again with the new value. */
export function RentField({ isTenant, sowing, rentQq, onRentQq, disabled }: RentProps) {
  const [draft, setDraft] = useState<string>("");
  const [invalid, setInvalid] = useState(false);
  const shownRent = sowing ? formatNumber(sowing.rent_qq, 1) : "";
  useEffect(() => setDraft(rentQq === undefined ? shownRent : formatNumber(rentQq, 1)), [rentQq, shownRent]);
  if (!sowing) return null;

  const commit = () => {
    const n = Number(draft.replace(",", "."));
    if (draft.trim() === "" || !Number.isFinite(n) || n < 0 || n > 60) {
      setInvalid(true);
      setDraft(rentQq === undefined ? shownRent : formatNumber(rentQq, 1));
      return;
    }
    setInvalid(false);
    if (rentQq === undefined && Math.abs(n - sowing.rent_qq) < 1e-9) return;
    onRentQq(n);
  };

  return (
    <label className="rent">
      <span className="label">{isTenant ? "Arriendo que pagás" : "Arriendo que te pagarían"}</span>
      <span className="rent-field">
        <input
          type="text"
          inputMode="decimal"
          value={draft}
          disabled={disabled}
          aria-describedby="rent-help"
          aria-invalid={invalid || undefined}
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
      <span id="rent-help" className={invalid ? "rent-error" : "sr-only"} role={invalid ? "alert" : undefined}>
        {invalid ? "El arriendo va de 0 a 60 qq de soja por hectárea; volvió al valor anterior." : "Cambiá el arriendo y el motor vuelve a decidir si conviene sembrar."}
      </span>
    </label>
  );
}
