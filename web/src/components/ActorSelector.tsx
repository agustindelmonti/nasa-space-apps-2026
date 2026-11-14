import { House, KeyRound, Landmark, Users } from "lucide-react";
import type { ActorProfile, ProfileId } from "../data/types";
import { formatNumber } from "../lib/format";
import { ProvenanceBadge } from "./ProvenanceBadge";

const ICON: Record<ProfileId, typeof House> = { OWNER: House, TENANT: KeyRound, COOP: Users, BANK: Landmark };

interface Props {
  profiles: ActorProfile[];
  value: ProfileId;
  onChange: (id: ProfileId) => void;
}

export function ActorSelector({ profiles, value, onChange }: Props) {
  const active = profiles.find((p) => p.profile_id === value);
  return (
    <section className="actorbar" aria-labelledby="h-actor">
      <h2 id="h-actor" className="label">
        Quién decide
      </h2>
      <div className="seg" role="group" aria-labelledby="h-actor">
        {profiles.map((p) => {
          const id = p.profile_id as ProfileId;
          const Icon = ICON[id] ?? Users;
          return (
            <button key={id} type="button" aria-pressed={id === value} data-actor={id} onClick={() => id !== value && onChange(id)}>
              <Icon size={20} strokeWidth={1.5} aria-hidden="true" />
              <span>{p.label}</span>
            </button>
          );
        })}
      </div>
      {active && (
        <div className="params">
          <span>
            Horizonte <b>{formatNumber(active.horizon_years.value)} {active.horizon_years.value === 1 ? "año" : "años"}</b>
          </span>
          <span>
            Peso del suelo α <b>{formatNumber(active.soil_weight_alpha.value, Number.isInteger(active.soil_weight_alpha.value) ? 0 : 1)}</b>{" "}
            <span className="unit">USD/ha por punto</span>
          </span>
          <span>
            Aversión al riesgo λ <b>{formatNumber(active.risk_aversion_lambda.value, Number.isInteger(active.risk_aversion_lambda.value) ? 0 : 1)}</b>
          </span>
          <span>
            Tasa <b>{formatNumber(active.discount_rate.value * 100)} %</b>
          </span>
          <ProvenanceBadge provenance={active.horizon_years.provenance} />
        </div>
      )}
    </section>
  );
}
