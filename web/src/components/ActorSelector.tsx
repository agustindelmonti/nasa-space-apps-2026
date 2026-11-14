import type { ReactNode } from "react";
import { House, KeyRound, Landmark, Users } from "lucide-react";
import type { ActorProfile, ProfileId } from "../data/types";
import { formatNumber } from "../lib/format";
import { ProvenanceBadge } from "./ProvenanceBadge";

const ICON: Record<ProfileId, typeof House> = { OWNER: House, TENANT: KeyRound, COOP: Users, BANK: Landmark };

interface Props {
  profiles: ActorProfile[];
  value: ProfileId;
  onChange: (id: ProfileId) => void;
  /** True when the user moved a slider: the parameters are then the user's, not the profile's. */
  overridden?: boolean;
  /** The sliders, rendered under the selector. */
  children?: ReactNode;
}

export function ActorSelector({ profiles, value, onChange, overridden = false, children }: Props) {
  const active = profiles.find((p) => p.profile_id === value);
  const capital = active?.constraints?.max_working_capital_usd_ha;
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
      {children}
      {active && (
        <div className="params">
          <span>
            Tasa <b>{formatNumber(active.discount_rate.value * 100)} %</b>
          </span>
          {capital && (
            <span>
              Capital de trabajo <b>{formatNumber(capital.value)}</b> <span className="unit">USD/ha</span>
            </span>
          )}
          {active.constraints && !active.constraints.allow_double_crop && <span>Sin doble cultivo</span>}
          <ProvenanceBadge provenance={overridden ? { kind: "USER_INPUT" } : active.horizon_years.provenance} />
        </div>
      )}
    </section>
  );
}
