import { Bug, ChevronDown, CircleHelp, Snowflake, Sprout, ThermometerSun, TriangleAlert, CloudRain, Droplets } from "lucide-react";
import type { RotationExplanation, RotationResult } from "../data/types";
import { ExplanationCard } from "./ExplanationCard";
import { DATASET_LABEL, RISK_LABEL, SEVERITY_LABEL } from "../lib/labels";
import { formatDate } from "../lib/format";
import { Figure } from "./Figure";
import { ProvenanceBadge } from "./ProvenanceBadge";
import { WaterState } from "./WaterState";

const RISK_ICON: Record<string, typeof Bug> = {
  WATER: Droplets,
  FROST: Snowflake,
  HEAT_STRESS: ThermometerSun,
  EXTREME_RAIN: CloudRain,
  ECONOMIC: TriangleAlert,
  WEEDS: Bug,
  SOIL: Sprout,
};

interface Props {
  result: RotationResult;
  name: string;
  /** The API's five-section card for this rotation, when the evaluation brought one. */
  card?: RotationExplanation;
}

/** Evidence and provenance of the selected rotation, exactly as the engine sends it. */
export function EvidencePanel({ result: r, name, card }: Props) {
  return (
    <section className="evidence" aria-labelledby="h-evid">
      <div className="sec-head">
        <h2 id="h-evid" className="h-headline">
          Evidencia
        </h2>
        <p className="soft">
          <span className="ev-rot">{name}</span>
          {r.is_current && <span className="current-tag"> · actual</span>} · puesto {r.rank} · <WaterState state={r.water_feasibility} />
        </p>
      </div>

      {card && <ExplanationCard card={card} part="primary" />}

      <details className="ev-more">
        <summary>
          <ChevronDown className="chev" size={18} strokeWidth={1.5} aria-hidden="true" />
          Ver detalle completo: puntaje, datos, supuestos y calendario
        </summary>
      {card && <ExplanationCard card={card} part="detail" />}
      <div className="ev-grid">
        <div className="ev-col">
          <h3 className="label">Puntaje y desglose</h3>
          {r.breakdown && r.loss_years && r.worst_year_margin && r.rain_on_bare_soil ? (
          <dl className="kv">
            <dt>VAN de márgenes</dt>
            <dd><Figure value={r.breakdown.npv} /></dd>
            <dt>α · ΔSuelo</dt>
            <dd><Figure value={r.breakdown.soil_term} signed /></dd>
            <dt>λ · Riesgo</dt>
            <dd><Figure value={{ ...r.breakdown.risk_term, value: -r.breakdown.risk_term.value }} signed /></dd>
            <dt>Puntaje</dt>
            <dd><Figure value={r.breakdown.total} /></dd>
            <dt>Margen en el peor año ({r.worst_year})</dt>
            <dd><Figure value={r.worst_year_margin} signed /></dd>
            <dt>Años con pérdida</dt>
            <dd>
              <span className="fig" title={`Años: ${r.loss_years.years.join(", ")}`}>
                {r.loss_years.count} de {r.loss_years.total}
              </span>
              <span className="soft small"> ({r.loss_years.years.join(", ")})</span>
            </dd>
            <dt>Lluvia sobre suelo desnudo</dt>
            <dd><Figure value={r.rain_on_bare_soil} /></dd>
          </dl>
          ) : (
            <p className="soft">Sin puntaje: faltan datos para calcularlo (ver faltantes).</p>
          )}
          <p className="small soft">Margen bruto por hectárea. El puntaje lo calcula el motor; la web solo lo muestra.</p>
        </div>

        <div className="ev-col ev-wide">
          <h3 className="label">Datos y supuestos</h3>
          <ul className="evid">
            {(r.evidence ?? []).map((e, i) => (
              <li key={i}>
                <span className="ev-badge"><ProvenanceBadge provenance={e.value.provenance} /></span>
                <p>
                  <b>{DATASET_LABEL[e.dataset] ?? e.dataset} · {e.variable}</b>, {formatDate(e.period.start)} a {formatDate(e.period.end)}. {e.interpretation}
                </p>
                <Figure value={e.value} badge={false} />
              </li>
            ))}
            {(r.missing ?? []).map((m, i) => (
              <li key={`m${i}`} className="missing">
                <span className="ev-badge"><ProvenanceBadge missing={{ item: m.item, howToGet: m.how_to_get }} /></span>
                <p>
                  <b>{m.item}</b>. {m.why_it_matters} Cómo conseguirlo: {m.how_to_get}
                </p>
                <span className="fig soft">sin dato</span>
              </li>
            ))}
          </ul>

          {(r.benefits ?? []).length > 0 && (
            <>
              <h3 className="label">Beneficios frente a la actual</h3>
              <ul className="plain">
                {(r.benefits ?? []).map((b, i) => (
                  <li key={i}>
                    {b.description} {b.value && <Figure value={b.value} signed />}
                  </li>
                ))}
              </ul>
            </>
          )}

          <h3 className="label">Riesgos a revisar en el lote</h3>
          {(r.risks ?? []).length === 0 ? (
            <p className="soft">La evaluación no informa riesgos para esta rotación.</p>
          ) : (
            <ul className="risks">
              {(r.risks ?? []).map((k, i) => {
                const Icon = RISK_ICON[k.risk_type] ?? CircleHelp;
                return (
                  <li key={i}>
                    <span className="risk-type">
                      <Icon size={16} strokeWidth={1.5} aria-hidden="true" />
                      {RISK_LABEL[k.risk_type]} · severidad {SEVERITY_LABEL[k.severity]}
                    </span>
                    <span>{k.description}</span>
                    {k.basis === "ASSUMPTION" ? (
                      <ProvenanceBadge provenance={{ kind: "ASSUMPTION", assumption_id: k.reference }} />
                    ) : (
                      <span className="small soft">Evidencia: {k.reference}</span>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
      </details>
    </section>
  );
}
