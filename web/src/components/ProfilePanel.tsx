import { useState } from "react";
import { ChevronDown, SlidersHorizontal } from "lucide-react";
import type { ActorProfile, ProfileOverrides, SliderLimits } from "../data/types";
import { formatNumber } from "../lib/format";
import { ProvenanceBadge } from "./ProvenanceBadge";
import { ProfileSliders } from "./ProfileSliders";

interface Props {
  profile: ActorProfile;
  limits: SliderLimits;
  overrides: ProfileOverrides;
  onChange: (next: ProfileOverrides) => void;
  onReset: () => void;
  disabled?: boolean;
}

/** The actor's parameters, folded by default: the ranking is the protagonist, the knobs are on demand. */
export function ProfilePanel({ profile, limits, overrides, onChange, onReset, disabled }: Props) {
  const [open, setOpen] = useState(false);
  const overridden = Object.keys(overrides).length > 0;
  const capital = profile.constraints?.max_working_capital_usd_ha;
  return (
    <section className={`profile${open ? " is-open" : ""}`} aria-labelledby="h-profile">
      <button type="button" className="profile-toggle" aria-expanded={open} aria-controls="profile-body" onClick={() => setOpen((o) => !o)}>
        <SlidersHorizontal size={18} strokeWidth={1.5} aria-hidden="true" />
        <span id="h-profile" className="h-title">
          Ajustar perfil
        </span>
        <span className="profile-sum soft">
          H {formatNumber(overrides.horizon_years ?? profile.horizon_years.value)} · α {formatNumber(overrides.alpha ?? profile.soil_weight_alpha.value, 1)} · λ{" "}
          {formatNumber(overrides.risk_aversion ?? profile.risk_aversion_lambda.value, 1)}
          {overridden && <b className="profile-mark"> · ajustado</b>}
        </span>
        <ChevronDown className="chev" size={18} strokeWidth={1.5} aria-hidden="true" />
      </button>
      <div id="profile-body" className="profile-body" hidden={!open}>
        <ProfileSliders profile={profile} limits={limits} overrides={overrides} onChange={onChange} onReset={onReset} disabled={disabled} />
        <div className="params">
          <span>
            Tasa <b>{formatNumber(profile.discount_rate.value * 100)} %</b>
          </span>
          {capital && (
            <span>
              Capital de trabajo <b>{formatNumber(capital.value)}</b> <span className="unit">USD/ha</span>
            </span>
          )}
          {profile.constraints && !profile.constraints.allow_double_crop && <span>Sin doble cultivo</span>}
          <ProvenanceBadge provenance={overridden ? { kind: "USER_INPUT" } : profile.horizon_years.provenance} />
        </div>
      </div>
    </section>
  );
}
