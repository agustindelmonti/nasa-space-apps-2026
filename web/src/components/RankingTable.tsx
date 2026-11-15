import { useLayoutEffect, useRef, type ReactNode } from "react";
import { Info } from "lucide-react";
import type { RotationResult, RotationStrips } from "../data/types";
import { EXCLUSION_LABEL, WARNING_LABEL } from "../lib/labels";
import { orderRows } from "../lib/rankDiff";
import { formatNumber, formatSigned } from "../lib/format";
import { CampaignStrip, StripLegend } from "./CampaignStrip";
import { WaterState } from "./WaterState";

interface Props {
  results: RotationResult[];
  /** rotation_id -> name, as the API sent it. */
  names: Record<string, string>;
  /** Row order: the API's `display_order` with preferences active, otherwise by `rank`. */
  order: string[];
  /** Engine warnings (codes); the ones with a label are shown. */
  warnings?: readonly string[];
  strips: RotationStrips;
  /** Positions moved since the previous evaluation, by rotation id (presentation only). */
  moves: Record<string, number>;
  /** Changes on every new evaluation so the ▲▼ marks restart. */
  evaluationKey: number;
  selectedId: string | null;
  onSelect: (rotationId: string) => void;
  loading: boolean;
  animateEntry: boolean;
  /** Hash of the input that produced these rows (X-Input-Hash), for traceability. */
  inputHash?: string;
  /** Controls that only reorder the rows (display preferences), shown under them. */
  toolbar?: ReactNode;
  /** Horizon of the actor (years): the score is the margins over it, plus soil, minus risk. */
  horizon?: number;
}

const reducedMotion = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Repeat a single-campaign strip so every row shares the same time axis. */
function cellsFor(strips: RotationStrips, id: string, length: number) {
  const base = strips.strips[id] ?? [];
  if (!base.length) return new Array(length).fill(null);
  return Array.from({ length }, (_, i) => base[i % base.length]);
}

export function RankingTable({
  results,
  names,
  order: displayOrder,
  warnings = [],
  strips,
  moves,
  evaluationKey,
  selectedId,
  onSelect,
  loading,
  animateEntry,
  inputHash,
  toolbar,
  horizon,
}: Props) {
  const rows = orderRows(results, displayOrder);
  const listRef = useRef<HTMLOListElement>(null);
  const lastTops = useRef<Record<string, number>>({});
  const axis = Math.max(12, ...rows.map((r) => strips.strips[r.rotation_id]?.length ?? 12));
  const order = rows.map((r) => r.rotation_id).join(",");
  const notices = warnings.filter((w) => w in WARNING_LABEL);
  // "Pérdida en 0 de 41 años" on every row is noise: show the fact only when some row has losses.
  const showLoss = rows.some((r) => (r.loss_years?.count ?? 0) > 0);

  // FLIP: compare each row's previous offset with the new one and animate the difference (300 ms).
  useLayoutEffect(() => {
    const list = listRef.current;
    if (!list) return;
    const items = Array.from(list.querySelectorAll<HTMLLIElement>("li[data-id]"));
    const motion = !reducedMotion();
    for (const el of items) {
      const id = el.dataset.id!;
      const before = lastTops.current[id];
      const dy = before === undefined ? 0 : before - el.offsetTop;
      if (dy && motion && el.animate) {
        el.animate([{ transform: `translateY(${dy}px)` }, { transform: "none" }], {
          duration: 300,
          easing: "cubic-bezier(0.16, 1, 0.3, 1)",
        });
      }
    }
    lastTops.current = Object.fromEntries(items.map((el) => [el.dataset.id!, el.offsetTop]));
  }, [order]);

  const announcement = rows
    .filter((r) => moves[r.rotation_id])
    .map((r) => {
      const m = moves[r.rotation_id];
      return `${names[r.rotation_id] ?? r.rotation_id} ${m > 0 ? "subió" : "bajó"} ${Math.abs(m)} puesto${Math.abs(m) > 1 ? "s" : ""}`;
    })
    .join(". ");

  return (
    <section className={`rank${loading ? " is-loading" : ""}`} aria-labelledby="h-rank" aria-busy={loading} data-input-hash={inputHash}>
      <div className="loadbar" aria-hidden="true" />
      <div className="rank-head">
        <div className="rank-title">
          <h2 id="h-rank" className="h-title">Rotaciones comparadas</h2>
          {horizon !== undefined && (
            <p className="rank-note">
              Puntaje en USD/ha acumulado a {formatNumber(horizon)} {horizon === 1 ? "año" : "años"}: márgenes + suelo − riesgo. No es el margen de un año.
            </p>
          )}
        </div>
        <StripLegend />
      </div>
      {rows.length < 3 && (
        <p className="warn" role="status">
          Evaluación incompleta: llegaron {rows.length} rotaciones y se necesitan al menos 3 para comparar.
        </p>
      )}
      {notices.map((w) => (
        <p key={w} className="notice" role="status" data-warning={w}>
          <Info size={16} strokeWidth={1.5} aria-hidden="true" />
          {WARNING_LABEL[w]}
        </p>
      ))}
      <p className="sr-only" aria-live="polite">
        {announcement}
      </p>
      <ol ref={listRef} className="rows" aria-label="Ranking de rotaciones">
        {rows.map((r, i) => {
          const m = moves[r.rotation_id] ?? 0;
          const name = names[r.rotation_id] ?? r.rotation_id;
          const reasons = (r.exclusion_reasons ?? []).map((x) => EXCLUSION_LABEL[x] ?? x);
          return (
            <li
              key={r.rotation_id}
              data-id={r.rotation_id}
              data-rank={r.rank}
              data-eligible={r.eligible}
              className={`row${i === 0 ? " first" : ""}${r.eligible ? "" : " ineligible"}${r.is_current ? " current" : ""}${selectedId === r.rotation_id ? " selected" : ""}`}
              onClick={(e) => {
                // The whole row selects; the name button stays the keyboard target.
                if (!(e.target as HTMLElement).closest("button")) onSelect(r.rotation_id);
              }}
            >
              {m !== 0 && <span className="flash" key={`f-${evaluationKey}`} aria-hidden="true" />}
              <span className="pos" aria-label={`Puesto ${i + 1}`}>
                {i + 1}
              </span>
              <div className="name">
                <button type="button" className="name-btn" aria-pressed={selectedId === r.rotation_id} onClick={() => onSelect(r.rotation_id)}>
                  <span className="rot-name">{name}</span>
                  {r.is_current && <span className="current-tag"> · actual</span>}
                </button>
              </div>
              <div className="score">
                {r.eligible ? (
                  <span className="fig">
                    {r.breakdown ? (
                      <>
                        {formatNumber(r.breakdown.total.value)} <span className="unit">USD/ha</span>
                      </>
                    ) : (
                      <span className="soft">sin puntaje</span>
                    )}
                  </span>
                ) : (
                  <span className="out">No elegible</span>
                )}
                <span className="move" key={`${evaluationKey}-${m}`} data-move={m || undefined}>
                  {m > 0 ? `▲ ${m}` : m < 0 ? `▼ ${-m}` : ""}
                </span>
              </div>
              <div className="facts">
                <WaterState state={r.water_feasibility} />
                <span>
                  ΔSuelo <span className="fig fig-sm">{r.soil_delta_index ? formatSigned(r.soil_delta_index.value) : "desconocido"}</span>
                </span>
                {showLoss && r.loss_years && (
                  <span>
                    Pérdida en{" "}
                    <span className="fig fig-sm">
                      {r.loss_years.count} de {r.loss_years.total}
                    </span>{" "}
                    años
                  </span>
                )}
                {!r.is_current && r.eligible && r.score_delta_vs_current && (
                  <span>
                    <span className="fig fig-sm">{formatSigned(r.score_delta_vs_current.value)}</span> vs actual
                  </span>
                )}
              </div>
              {!r.eligible && reasons.length > 0 && <p className="why">No elegible: {reasons.join("; ")}</p>}
              <CampaignStrip
                cells={cellsFor(strips, r.rotation_id, axis)}
                startMonth={strips.start_month}
                vulnerability={r.vulnerability_calendar}
                animateEntry={animateEntry}
              />
            </li>
          );
        })}
      </ol>
      {toolbar && <div className="rank-foot">{toolbar}</div>}
    </section>
  );
}
