import { useId, useState, type ReactNode } from "react";
import { Calculator, CircleHelp, FlaskConical, Satellite, UserRound } from "lucide-react";
import type { PValue } from "../data/types";
import { useAssumptions } from "./AssumptionsContext";
import { DATASET_LABEL } from "../lib/labels";
import { formatDate } from "../lib/format";

type Provenance = PValue["provenance"];

/** `kind` has a default in the schema, so it may be absent: infer it from the shape. */
const kindOf = (p: Provenance) =>
  p.kind ?? ("source" in p ? "OBSERVED" : "method" in p ? "DERIVED" : "assumption_id" in p ? "ASSUMPTION" : "USER_INPUT");

const KIND = {
  OBSERVED: { short: "Obs", cls: "b-obs", Icon: Satellite, title: "Observado" },
  DERIVED: { short: "Der", cls: "b-der", Icon: Calculator, title: "Calculado" },
  ASSUMPTION: { short: "Sup", cls: "b-sup", Icon: FlaskConical, title: "Supuesto" },
  USER_INPUT: { short: "Usu", cls: "b-usu", Icon: UserRound, title: "Dato del productor" },
} as const;

interface Props {
  provenance?: Provenance;
  /** Shown when there is no value at all (a missing datum). */
  missing?: { item: string; howToGet: string };
}

/** Provenance badge with a tooltip that opens on hover, keyboard focus and tap. */
export function ProvenanceBadge({ provenance, missing }: Props) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const assumptions = useAssumptions();

  let label: string;
  let cls: string;
  let body: ReactNode;
  let Icon = CircleHelp;
  let title = "Desconocido";

  if (!provenance) {
    label = "Desconocido";
    cls = "b-unk";
    body = (
      <>
        <p>Sin dato{missing ? `: ${missing.item}` : ""}.</p>
        {missing && <p>Cómo conseguirlo: {missing.howToGet}</p>}
      </>
    );
  } else {
    const kind = kindOf(provenance);
    const k = KIND[kind];
    Icon = k.Icon;
    title = k.title;
    cls = k.cls;
    label = "assumption_id" in provenance ? `${k.short} · ${provenance.assumption_id}` : k.short;
    if ("source" in provenance) {
      const s = provenance.source;
      body = (
        <dl>
          <dt>Dataset</dt>
          <dd>{DATASET_LABEL[s.dataset] ?? s.dataset}</dd>
          <dt>Variable</dt>
          <dd>{s.variable}</dd>
          <dt>Período</dt>
          <dd>
            {formatDate(s.period.start)} a {formatDate(s.period.end)}
          </dd>
          <dt>Resolución</dt>
          <dd>
            {s.spatial_resolution} · {s.temporal_resolution}
            {s.is_modeled ? " · modelado" : ""}
          </dd>
          {s.location_note && (
            <>
              <dt>Ubicación</dt>
              <dd>{s.location_note}</dd>
            </>
          )}
        </dl>
      );
    } else if ("method" in provenance) {
      body = (
        <dl>
          <dt>Método</dt>
          <dd>{provenance.method}</dd>
          <dt>Insumos</dt>
          <dd>{provenance.derived_from.join(", ")}</dd>
        </dl>
      );
    } else if ("assumption_id" in provenance) {
      const a = assumptions[provenance.assumption_id];
      body = (
        <dl>
          <dt>Supuesto</dt>
          <dd>{provenance.assumption_id}</dd>
          <dt>Qué es</dt>
          <dd>{a?.description ?? "sin descripción en el registro"}</dd>
          <dt>Fuente</dt>
          <dd>{a?.source ?? "pendiente AFA"}</dd>
          <dt>Validación</dt>
          <dd>{a?.status === "PENDING_AFA" ? "pendiente de validar con AFA" : (a?.status ?? "desconocida")}</dd>
        </dl>
      );
    } else {
      const note = "note" in provenance ? provenance.note : null;
      body = <p>Lo cargó el productor{note ? `: ${note}` : "."}</p>;
    }
  }

  return (
    <span
      className="prov"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
    >
      <button
        type="button"
        className={`badge ${cls}`}
        aria-describedby={id}
        aria-expanded={open}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={() => setOpen((o) => !o)}
      >
        {label}
      </button>
      <span role="tooltip" id={id} className="tip" hidden={!open}>
        <span className="tip-head">
          <Icon size={16} strokeWidth={1.5} aria-hidden="true" />
          {title}
        </span>
        {body}
      </span>
    </span>
  );
}
