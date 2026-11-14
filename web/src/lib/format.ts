// Formatting only (Argentine locale: decimal comma, dot for thousands). No rounding policy
// beyond the number of decimals shown.
const nf = (digits: number) =>
  new Intl.NumberFormat("es-AR", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export function formatNumber(value: number, digits = 0): string {
  return nf(digits).format(value).replace("-", "−");
}

export function formatSigned(value: number, digits = 0): string {
  const s = formatNumber(Math.abs(value), digits);
  if (value > 0) return `+${s}`;
  if (value < 0) return `−${s}`;
  return s;
}

const UNIT_LABEL: Record<string, string> = {
  "m3/m3": "m³/m³",
  "USD/ha/point": "USD/ha por punto",
  fraction: "",
  ratio: "",
  index: "",
  count: "",
  year: "años",
};

export function unitLabel(unit: string): string {
  return unit in UNIT_LABEL ? UNIT_LABEL[unit] : unit;
}

/** Decimals that read well for a unit (presentation only). */
export function digitsFor(unit: string, value: number): number {
  if (unit === "m3/m3") return 2;
  if (unit === "fraction" || unit === "ratio") return Number.isInteger(value) ? 0 : value < 1 ? 2 : 1;
  if (unit === "USD/ha/point") return Number.isInteger(value) ? 0 : 1;
  return Number.isInteger(value) ? 0 : 1;
}

export function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}
