import { ChevronDown } from "lucide-react";
import type { PValue, RotationSearch, SearchColumn, SearchRow } from "../data/types";
import { formatNumber, formatSigned } from "../lib/format";
import { Figure } from "./Figure";
import { WaterState } from "./WaterState";

const TOP = 5;

/** Rebuilds a figure with the unit and provenance declared once for its column. */
function pv(search: RotationSearch, col: SearchColumn, value: number | null): PValue | null {
  if (value === null) return null;
  const meta = search.columns[col];
  return { value, unit: meta.unit, provenance: meta.provenance } as PValue;
}

interface Props {
  search: RotationSearch;
  actorLabel: string;
  /** True when the sliders differ from the predefined profile: the search does not follow them. */
  customProfile: boolean;
}

/** One sentence that answers the section's question; it is also the folded summary. */
function answer(search: RotationSearch): string {
  const { ranking, counts } = search;
  if (!ranking.length) return "Ninguna rotación con agua factible o riesgosa cumple las restricciones de este perfil.";
  const catalogBest = ranking.find((r) => r.rotation_id === search.best_catalog);
  const gain = search.gain_vs_catalog?.value ?? 0;
  if (!catalogBest) return `Ninguna de las 5 entra con agua factible o riesgosa; la mejor encontrada es ${ranking[0].name}.`;
  if (counts.eligible === 1) return `No: ${catalogBest.name} es la única que pasa el filtro de agua.`;
  if (search.best_found === search.best_catalog || gain < 0.5)
    return `No: ${catalogBest.name} también es la mejor de las ${formatNumber(counts.eligible)} que pasan el filtro de agua.`;
  return `Sí: ${ranking[0].name} suma ${formatSigned(gain)} USD/ha de puntaje más que ${catalogBest.name}, que queda en el puesto ${catalogBest.rank} de ${formatNumber(counts.eligible)}.`;
}

/** "¿Hay algo mejor fuera de estas 5?": exhaustive search precomputed with the predefined profile,
 *  folded under the evidence so it does not compete with the ranking the sliders drive. */
export function SearchPanel({ search, actorLabel, customProfile }: Props) {
  const { counts, ranking } = search;
  const actor = actorLabel.toLowerCase();
  return (
    <details className="search">
      <summary>
        <ChevronDown className="chev" size={18} strokeWidth={1.5} aria-hidden="true" />
        <h2 id="h-search" className="h-title">¿Hay algo mejor fuera de estas 5?</h2>
        <span className="search-sum">{answer(search)}</span>
      </summary>
      <div className="search-body">
        <p className="search-caveat">
          {customProfile && <strong>Tus ajustes no aplican acá. </strong>}
          Calculado con el perfil predefinido de {actor} y precios de ejemplo; los sliders y el arriendo no cambian esta búsqueda.
        </p>
        <p className="soft">
          Probamos todas las rotaciones de 1 a 3 campañas que arman los cultivos del catálogo ({formatNumber(counts.generated)}), descartamos{" "}
          {formatNumber(counts.generated - counts.kept_by_rules)} por reglas agronómicas pendientes de validar con AFA y evaluamos{" "}
          {formatNumber(counts.evaluated)} con el mismo motor. Compiten solo las que tienen agua factible o riesgosa:{" "}
          {formatNumber(counts.eligible)} para {actor}
          {counts.water_excluded ? `, ${formatNumber(counts.water_excluded)} quedaron afuera por agua` : ""}.
        </p>
        {ranking.length > 0 && (
          <ol className="search-list">
            {ranking.slice(0, TOP).map((r) => (
              <SearchItem key={r.rotation_id} row={r} search={search} />
            ))}
          </ol>
        )}
        <p className="search-note">
          "Pareto": ninguna otra la supera a la vez en margen, suelo y riesgo ({formatNumber(counts.pareto)} de {formatNumber(counts.eligible)}). En
          dorado, las que están entre las 5 del ranking.
        </p>
      </div>
    </details>
  );
}

function SearchItem({ row, search }: { row: SearchRow; search: RotationSearch }) {
  const score = pv(search, "score", row.score);
  const margin = pv(search, "expected_annual_margin", row.expected_annual_margin);
  return (
    <li className="search-item" data-catalog={row.in_catalog || undefined}>
      <span className="search-rank">{row.rank}</span>
      <span className="search-name">
        <span>
          {row.name}
          {row.is_current && " (actual)"}
        </span>
        <span className="search-tags">
          {row.water_feasibility && <WaterState state={row.water_feasibility} />}
          {row.soil_delta_index !== null && <span>ΔSuelo {formatSigned(row.soil_delta_index)}</span>}
          {row.pareto && <span>Pareto</span>}
        </span>
      </span>
      <span className="search-figs">
        {score && (
          <span>
            <small>puntaje</small>
            <Figure value={{ ...score, value: Math.round(score.value) }} badge={false} />
          </span>
        )}
        {margin && (
          <span>
            <small>margen por año</small>
            <Figure value={{ ...margin, value: Math.round(margin.value) }} badge={false} />
          </span>
        )}
      </span>
    </li>
  );
}
