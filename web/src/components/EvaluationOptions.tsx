import type { DisplayPreference, YearClassFilter } from "../data/types";
import { YEAR_CLASS_LABEL } from "../lib/labels";

interface Props {
  yearClass: YearClassFilter;
  onYearClass: (v: YearClassFilter) => void;
  preferences: DisplayPreference[];
  onPreferences: (v: DisplayPreference[]) => void;
  disabled?: boolean;
}

const CLASSES: YearClassFilter[] = ["ALL", "DRY", "NORMAL", "WET"];
const PREFS: { id: DisplayPreference; label: string }[] = [
  { id: "WATER_SAFE_FIRST", label: "Primero las que no son riesgosas en agua" },
  { id: "DOUBLE_CROP_FIRST", label: "Primero las de doble cultivo" },
];

/** Year class sent as `year_class_filter` and presentation preferences sent as `display_preferences`. */
export function EvaluationOptions({ yearClass, onYearClass, preferences, onPreferences, disabled = false }: Props) {
  return (
    <div className="options" role="group" aria-label="Opciones de la comparación">
      <div className="opt">
        <h3 id="h-years" className="label">
          Campañas que se miran
        </h3>
        <div className="seg seg-sm" role="group" aria-labelledby="h-years">
          {CLASSES.map((c) => (
            <button key={c} type="button" aria-pressed={c === yearClass} data-year-class={c} disabled={disabled} onClick={() => c !== yearClass && onYearClass(c)}>
              {YEAR_CLASS_LABEL[c]}
            </button>
          ))}
        </div>
      </div>
      <div className="opt">
        <h3 id="h-prefs" className="label">
          Orden de la tabla
        </h3>
        <div className="toggles" role="group" aria-labelledby="h-prefs">
          {PREFS.map((p) => {
            const on = preferences.includes(p.id);
            return (
              <button
                key={p.id}
                type="button"
                aria-pressed={on}
                data-pref={p.id}
                disabled={disabled}
                onClick={() => onPreferences(on ? preferences.filter((x) => x !== p.id) : [...preferences, p.id])}
              >
                {p.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
