import type { CSSProperties } from "react";
import type { Crop, RotationResult } from "../data/types";
import { CROP_LABEL, CROP_SERIES, MONTH_INITIAL, MONTH_NAME } from "../lib/labels";

interface Props {
  cells: (Crop | null)[];
  /** Calendar month (1..12) of the first cell. */
  startMonth: number;
  vulnerability: RotationResult["vulnerability_calendar"];
  /** Fill left to right once (entry moment); false afterwards. */
  animateEntry?: boolean;
}

const monthOf = (startMonth: number, i: number) => (startMonth - 1 + i) % 12; // 0 = January

/** Accessible summary: runs of the same crop, e.g. "trigo de junio a noviembre". */
function describe(cells: (Crop | null)[], startMonth: number, frost: boolean[]): string {
  const runs: string[] = [];
  let i = 0;
  while (i < cells.length) {
    let j = i;
    while (j + 1 < cells.length && cells[j + 1] === cells[i]) j++;
    const from = MONTH_NAME[monthOf(startMonth, i)];
    const to = MONTH_NAME[monthOf(startMonth, j)];
    const what = cells[i] ? CROP_LABEL[cells[i] as Crop] : "suelo desnudo";
    runs.push(i === j ? `${what} en ${from}` : `${what} de ${from} a ${to}`);
    i = j + 1;
  }
  const frostCount = frost.filter(Boolean).length;
  const campaigns = cells.length / 12;
  return `Franja de ${campaigns} campaña${campaigns > 1 ? "s" : ""}: ${runs.join(", ")}.${
    frostCount ? ` Helada histórica en ${frostCount} mes${frostCount > 1 ? "es" : ""} con cultivo.` : ""
  }`;
}

/** The campaign strip (DESIGN.md signature component): months with crops in color,
 *  bare soil hatched and frost as an outlined rhombus. It only draws what it receives. */
export function CampaignStrip({ cells, startMonth, vulnerability, animateEntry = false }: Props) {
  const frost = cells.map((crop, i) => {
    if (!crop) return false;
    const m = monthOf(startMonth, i);
    return (vulnerability ?? []).some((v) => v.event === "FROST" && v.crop === crop && v.in_field_by_month[m] && v.level_by_month[m] !== null);
  });
  const campaigns = cells.length / 12;
  return (
    <div className="strip-wrap" style={{ "--cells": cells.length } as CSSProperties}>
      <div className={`strip${animateEntry ? " enter" : ""}`} role="img" aria-label={describe(cells, startMonth, frost)}>
        {cells.map((crop, i) => (
          <i
            key={i}
            className={`${crop ? `crop-${CROP_SERIES[crop]}` : "bare"}${frost[i] ? " frost" : ""}${i % 12 === 0 && i > 0 ? " camp-start" : ""}`}
            style={{ "--i": i } as CSSProperties}
          />
        ))}
      </div>
      <div className="months" aria-hidden="true">
        {cells.map((_, i) => (
          <span key={i} className={i % 12 === 0 && i > 0 ? "camp-start" : undefined}>
            {MONTH_INITIAL[monthOf(startMonth, i)]}
          </span>
        ))}
      </div>
      {campaigns > 1 && (
        <div className="campaigns" aria-hidden="true">
          {Array.from({ length: campaigns }, (_, k) => (
            <span key={k}>Campaña {k + 1}</span>
          ))}
        </div>
      )}
    </div>
  );
}

/** Legend for the strip; lives in the ranking header (DESIGN.md "la regla de la leyenda"). */
export function StripLegend() {
  return (
    <ul className="legend" aria-label="Leyenda de la franja">
      <li><i className="key crop-soy" />Soja</li>
      <li><i className="key crop-maize" />Maíz</li>
      <li><i className="key crop-wheat" />Trigo</li>
      <li><i className="key crop-vetch" />Vicia</li>
      <li><i className="key crop-rye-oat" />Centeno</li>
      <li><i className="key bare" />Suelo desnudo</li>
      <li><i className="key-frost" />Helada</li>
    </ul>
  );
}
