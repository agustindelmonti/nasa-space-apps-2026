import type { PValue, RotationSearch, SearchColumn, SearchRow } from "../data/types";
import { WATER_LABEL } from "../lib/labels";
import { formatNumber } from "../lib/format";
import { Figure } from "./Figure";

const TOP = 5;

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

/** "¿Hay algo mejor fuera de estas 5?": exhaustive search precomputed with the predefined profile. */
export function SearchPanel({ search, actorLabel, customProfile }: Props) {
  const { counts, ranking } = search;
  const top = ranking.slice(0, TOP);
  const catalogBest = ranking.find((r) => r.rotation_id === search.best_catalog) ?? null;
  const gain = search.gain_vs_catalog;
  const pruned = Object.values(counts.pruned_by_rule).reduce((a, b) => a + b, 0);
  const better = gain !== null && gain.value > 0.5 && search.best_found !== search.best_catalog;

  return (
    <section className="search" aria-labelledby="h-search">
      <header className="search-head">
        <h2 id="h-search" className="h-title">¿Hay algo mejor fuera de estas 5?</h2>
        <p className="soft">
          Probamos todas las rotaciones de 1 a 3 campañas que arman los cultivos del catálogo:{" "}
          {formatNumber(counts.generated)} combinaciones, {formatNumber(counts.evaluated)} evaluadas con el mismo motor
          después de descartar las que rompen reglas agronómicas (A-AGR-02 a A-AGR-05, pendientes AFA).{" "}
          {formatNumber(counts.eligible)} cumplen las restricciones de {actorLabel.toLowerCase()}.
        </p>
      </header>
      {ranking.length === 0 ? (
        <p className="soft">Ninguna rotación cumple las restricciones de este perfil con este filtro de años.</p>
      ) : (
        <>
          <p className="search-verdict">
            {better && gain && catalogBest ? (
              <>
                Sí: la mejor encontrada supera a <strong>{catalogBest.name}</strong> (la mejor de las 5) por{" "}
                <Figure value={gain} signed className="fig-inline" />. Esa quedó #{catalogBest.rank} de {formatNumber(counts.eligible)}.
              </>
            ) : catalogBest ? (
              <>
                No: <strong>{catalogBest.name}</strong>, la mejor de las 5, es también la mejor de las {formatNumber(counts.eligible)}.
              </>
            ) : (
              <>Ninguna de las 5 del catálogo cumple las restricciones; abajo, las mejores encontradas.</>
            )}
          </p>
          <ol className="search-list">
            {top.map((r) => (
              <SearchItem key={r.rotation_id} row={r} search={search} />
            ))}
          </ol>
        </>
      )}
      <p className="search-note">
        {customProfile ? <strong>Los sliders no aplican acá. </strong> : null}
        Calculado con el perfil predefinido de {actorLabel.toLowerCase()} y precios de ejemplo; los sliders y el arriendo no
        cambian esta búsqueda. "Pareto": ninguna otra la supera a la vez en margen, suelo y riesgo
        ({formatNumber(counts.pareto)} de {formatNumber(counts.eligible)}). {pruned > 0 && `Reglas: ${formatNumber(counts.generated - counts.kept_by_rules)} descartadas.`}
      </p>
    </section>
  );
}

function SearchItem({ row, search }: { row: SearchRow; search: RotationSearch }) {
  const score = pv(search, "score", row.score);
  const margin = pv(search, "expected_annual_margin", row.expected_annual_margin);
  const soil = pv(search, "soil_delta_index", row.soil_delta_index);
  return (
    <li className="search-item" data-catalog={row.in_catalog || undefined}>
      <span className="search-rank">#{row.rank}</span>
      <span className="search-name">
        {row.name}
        <span className="search-tags">
          {row.in_catalog && <span className="tag">de las 5</span>}
          {row.is_current && <span className="tag">actual</span>}
          {row.pareto && <span className="tag tag-pareto">Pareto</span>}
          {row.water_feasibility && <span className="tag" data-water={row.water_feasibility}>agua: {WATER_LABEL[row.water_feasibility].toLowerCase()}</span>}
        </span>
      </span>
      <span className="search-figs">
        {score && (
          <span>
            <small>puntaje</small>
            <Figure value={score} badge={false} />
          </span>
        )}
        {margin && (
          <span>
            <small>margen/año</small>
            <Figure value={margin} badge={false} />
          </span>
        )}
        {soil && (
          <span>
            <small>ΔSuelo</small>
            <Figure value={soil} signed badge={false} />
          </span>
        )}
      </span>
    </li>
  );
}
