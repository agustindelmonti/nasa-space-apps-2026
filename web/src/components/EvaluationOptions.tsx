import type { DisplayPreference, YearClassFilter } from "../data/types";
import { YEAR_CLASS_LABEL } from "../lib/labels";

const CLASSES: YearClassFilter[] = ["ALL", "DRY", "NORMAL", "WET"];
const PREFS: { id: DisplayPreference; label: string }[] = [
  { id: "WATER_SAFE_FIRST", label: "Primero las que no son riesgosas en agua" },
  { id: "DOUBLE_CROP_FIRST", label: "Primero las de doble cultivo" },
];

/** Year class sent as `year_class_filter`. It sits next to "Quién decide": both change the comparison. */
export function YearClassSelector({ value, onChange, disabled = false }: { value: YearClassFilter; onChange: (v: YearClassFilter) => void; disabled?: boolean }) {
  return (
    <div className="opt">
      <h3 id="h-years" className="label">
        Campañas que se miran
      </h3>
      <div className="seg seg-sm" role="group" aria-labelledby="h-years">
        {CLASSES.map((c) => (
          <button key={c} type="button" aria-pressed={c === value} data-year-class={c} disabled={disabled} onClick={() => c !== value && onChange(c)}>
            {YEAR_CLASS_LABEL[c]}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Presentation preferences sent as `display_preferences`; they only reorder the table. */
export function DisplayPreferences({ value, onChange, disabled = false }: { value: DisplayPreference[]; onChange: (v: DisplayPreference[]) => void; disabled?: boolean }) {
  return (
    <div className="prefs" role="group" aria-labelledby="h-prefs">
      <h3 id="h-prefs" className="label">
        Orden de la tabla
      </h3>
      <div className="toggles">
        {PREFS.map((p) => {
          const on = value.includes(p.id);
          return (
            <button
              key={p.id}
              type="button"
              aria-pressed={on}
              data-pref={p.id}
              disabled={disabled}
              onClick={() => onChange(on ? value.filter((x) => x !== p.id) : [...value, p.id])}
            >
              {p.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
