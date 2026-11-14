import { useLayoutEffect, useRef } from "react";
import type { Rotation, RotationResult, RotationStrips } from "../data/types";
import { byRank } from "../lib/rankDiff";
import { formatNumber, formatSigned } from "../lib/format";
import { CampaignStrip, StripLegend } from "./CampaignStrip";
import { WaterState } from "./WaterState";

interface Props {
  results: RotationResult[];
  rotations: Rotation[];
  strips: RotationStrips;
  /** Positions moved since the previous evaluation, by rotation id (presentation only). */
  moves: Record<string, number>;
  /** Changes on every new evaluation so the ▲▼ marks restart. */
  evaluationKey: number;
  selectedId: string | null;
  onSelect: (rotationId: string) => void;
  loading: boolean;
  animateEntry: boolean;
}

const reducedMotion = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Repeat a single-campaign strip so every row shares the same time axis. */
function cellsFor(strips: RotationStrips, id: string, length: number) {
  const base = strips.strips[id] ?? [];
  if (!base.length) return new Array(length).fill(null);
  return Array.from({ length }, (_, i) => base[i % base.length]);
}

export function RankingTable({ results, rotations, strips, moves, evaluationKey, selectedId, onSelect, loading, animateEntry }: Props) {
  const rows = byRank(results);
  const listRef = useRef<HTMLOListElement>(null);
  const lastTops = useRef<Record<string, number>>({});
  const names = Object.fromEntries(rotations.map((r) => [r.rotation_id, r.name]));
  const axis = Math.max(12, ...rows.map((r) => strips.strips[r.rotation_id]?.length ?? 12));
  const order = rows.map((r) => r.rotation_id).join(",");

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
    <section className={`rank${loading ? " is-loading" : ""}`} aria-labelledby="h-rank" aria-busy={loading}>
      <div className="loadbar" aria-hidden="true" />
      <div className="rank-head">
        <h2 id="h-rank" className="h-title">Rotaciones comparadas</h2>
        <StripLegend />
      </div>
      {rows.length < 3 && (
        <p className="warn" role="status">
          Evaluación incompleta: llegaron {rows.length} rotaciones y se necesitan al menos 3 para comparar.
        </p>
      )}
      <p className="sr-only" aria-live="polite">
        {announcement}
      </p>
      <ol ref={listRef} className="rows" aria-label="Ranking de rotaciones">
        {rows.map((r) => {
          const m = moves[r.rotation_id] ?? 0;
          const name = names[r.rotation_id] ?? r.rotation_id;
          return (
            <li
              key={r.rotation_id}
              data-id={r.rotation_id}
              data-rank={r.rank}
              className={`row${r.rank === 1 ? " first" : ""}${r.is_current ? " current" : ""}${selectedId === r.rotation_id ? " selected" : ""}`}
            >
              <span className="pos" aria-label={`Puesto ${r.rank}`}>
                {r.rank}
              </span>
              <div className="name">
                <button type="button" className="name-btn" aria-pressed={selectedId === r.rotation_id} onClick={() => onSelect(r.rotation_id)}>
                  <span className="rot-name">{name}</span>
                  {r.is_current && <span className="current-tag"> · actual</span>}
                </button>
              </div>
              <div className="score">
                <span className="fig">
                  {r.breakdown ? <>{formatNumber(r.breakdown.total.value)} <span className="unit">USD/ha</span></> : <span className="soft">sin puntaje</span>}
                </span>
                <span className="move" key={`${evaluationKey}-${m}`} data-move={m || undefined}>
                  {m > 0 ? `▲ ${m}` : m < 0 ? `▼ ${-m}` : ""}
                </span>
              </div>
              <div className="facts">
                <WaterState state={r.water_feasibility} />
                <span>
                  ΔSuelo <span className="fig fig-sm">{r.soil_delta_index ? formatSigned(r.soil_delta_index.value) : "desconocido"}</span>
                </span>
                {r.loss_years && (
                  <span>
                    Pérdida en{" "}
                    <span className="fig fig-sm">
                      {r.loss_years.count} de {r.loss_years.total}
                    </span>{" "}
                    años
                  </span>
                )}
                {!r.is_current && r.score_delta_vs_current && (
                  <span>
                    <span className="fig fig-sm">{formatSigned(r.score_delta_vs_current.value)}</span> vs actual
                  </span>
                )}
              </div>
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
    </section>
  );
}
