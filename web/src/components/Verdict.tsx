import type { ReactNode } from "react";
import type { RotationResult } from "../data/types";
import { orderRows } from "../lib/rankDiff";
import { formatSigned } from "../lib/format";
import { WaterState } from "./WaterState";

interface Props {
  results: RotationResult[];
  order: string[];
  names: Record<string, string>;
  actorLabel: string;
  /** The actor selector, shown in the band: changing who decides is the main move. */
  children: ReactNode;
}

/** The answer first: which rotation the engine ranks first for this actor, against the current one.
 *  Only restates engine figures (rank, score delta, water state, loss years). */
export function Verdict({ results, order, names, actorLabel, children }: Props) {
  const rows = orderRows(results, order);
  const top = rows.find((r) => r.eligible) ?? null;
  const current = results.find((r) => r.is_current) ?? null;
  const name = (r: RotationResult) => names[r.rotation_id] ?? r.rotation_id;
  const delta = top && !top.is_current ? top.score_delta_vs_current : null;

  return (
    <section className="verdict" aria-labelledby="h-verdict" aria-live="polite">
      {children}
      <div className="verdict-body">
        {top ? (
          <>
            <h2 id="h-verdict" className="verdict-line">
              Para el <span className="who">{actorLabel.toLowerCase()}</span>,{" "}
              {top.is_current ? (
                <>
                  la rotación actual <em>{name(top)}</em> sigue siendo la mejor opción.
                </>
              ) : (
                <>
                  conviene <em>{name(top)}</em>.
                </>
              )}
            </h2>
            <ul className="verdict-facts">
              {delta && current && (
                <li>
                  <span className="fig">{formatSigned(delta.value)}</span> <span className="unit">USD/ha</span> de puntaje frente a la
                  actual ({name(current)})
                </li>
              )}
              <li>
                Agua: <WaterState state={top.water_feasibility} />
              </li>
              {top.loss_years && (
                <li>
                  Pérdida en{" "}
                  <span className="fig">
                    {top.loss_years.count} de {top.loss_years.total}
                  </span>{" "}
                  campañas
                </li>
              )}
            </ul>
          </>
        ) : (
          <h2 id="h-verdict" className="verdict-line">
            Para el <span className="who">{actorLabel.toLowerCase()}</span> ninguna rotación es elegible con estas restricciones.
          </h2>
        )}
      </div>
    </section>
  );
}
