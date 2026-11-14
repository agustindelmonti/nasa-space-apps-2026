import { RotateCcw } from "lucide-react";
import type { ActorProfile, ProfileOverrides, SliderLimits } from "../data/types";
import { formatNumber } from "../lib/format";

interface Props {
  profile: ActorProfile;
  limits: SliderLimits;
  overrides: ProfileOverrides;
  onChange: (next: ProfileOverrides) => void;
  onReset: () => void;
  /** Offline demo: the fixtures cannot re-evaluate, so the sliders are off. */
  disabled?: boolean;
}

interface Spec {
  key: keyof ProfileOverrides;
  limit: keyof SliderLimits;
  id: string;
  name: string;
  symbol: string;
  help: string;
  step: number;
  digits: number;
  unit: (v: number) => string;
  base: (p: ActorProfile) => number;
}

const SPECS: Spec[] = [
  {
    key: "horizon_years",
    limit: "horizon_years",
    id: "H",
    name: "Horizonte",
    symbol: "H",
    help: "Horizonte: cuántos años mirás",
    step: 1,
    digits: 0,
    unit: (v) => (v === 1 ? "año" : "años"),
    base: (p) => p.horizon_years.value,
  },
  {
    key: "alpha",
    limit: "alpha",
    id: "alpha",
    name: "Peso del suelo",
    symbol: "α",
    help: "Peso del suelo: cuánto vale para vos cuidar el suelo",
    step: 0.5,
    digits: 1,
    unit: () => "USD/ha por punto",
    base: (p) => p.soil_weight_alpha.value,
  },
  {
    key: "risk_aversion",
    limit: "lambda",
    id: "lambda",
    name: "Aversión al riesgo",
    symbol: "λ",
    help: "Aversión al riesgo: cuánto te pesan los años malos",
    step: 0.1,
    digits: 1,
    unit: () => "",
    base: (p) => p.risk_aversion_lambda.value,
  },
];

/** H, α and λ over the actor's profile. It only sends overrides; the engine re-ranks. */
export function ProfileSliders({ profile, limits, overrides, onChange, onReset, disabled = false }: Props) {
  const touched = Object.keys(overrides).length > 0;
  return (
    <div className="sliders" role="group" aria-labelledby="h-profile">
      <div className="sliders-head">
        <p className="slider-help">Mové un parámetro y el motor vuelve a ordenar.</p>
        {touched && (
          <button type="button" className="btn-secondary btn-sm" onClick={onReset}>
            <RotateCcw size={16} strokeWidth={1.5} aria-hidden="true" />
            Volver al perfil
          </button>
        )}
      </div>
      {SPECS.map((s) => {
        const [min, max] = limits[s.limit] ?? [0, 1];
        const base = s.base(profile);
        const value = overrides[s.key] ?? base;
        const digits = Number.isInteger(value) ? 0 : s.digits;
        const inputId = `slider-${s.id}`;
        return (
          <div key={s.key} className={`slider${overrides[s.key] !== undefined ? " is-set" : ""}`} data-slider={s.id}>
            <label htmlFor={inputId} className="slider-top">
              <span className="slider-name">
                {s.name} <span className="sym">{s.symbol}</span>
              </span>
              <span className="fig fig-sm" data-value>
                {formatNumber(value, digits)} {s.unit(value) && <span className="unit">{s.unit(value)}</span>}
              </span>
            </label>
            <input
              id={inputId}
              type="range"
              min={min}
              max={max}
              step={s.step}
              value={value}
              disabled={disabled}
              aria-valuetext={`${formatNumber(value, digits)} ${s.unit(value)}`.trim()}
              aria-describedby={`${inputId}-help`}
              onChange={(e) => {
                const v = Number(e.target.value);
                const next = { ...overrides };
                if (v === base) delete next[s.key];
                else next[s.key] = v;
                onChange(next);
              }}
            />
            <span className="slider-scale" aria-hidden="true">
              <span>{formatNumber(min)}</span>
              <span>{formatNumber(max)}</span>
            </span>
            <span id={`${inputId}-help`} className="slider-help">
              {s.help}
            </span>
          </div>
        );
      })}
      {disabled && <p className="slider-help">Los ajustes necesitan conexión con el motor.</p>}
    </div>
  );
}
