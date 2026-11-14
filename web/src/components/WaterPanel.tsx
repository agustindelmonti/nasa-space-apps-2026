import { CloudRain, Droplets, Waves } from "lucide-react";
import type { PlotContext } from "../data/types";
import { Figure } from "./Figure";

export function WaterPanel({ cells }: { cells: PlotContext["water_panel"] }) {
  const items = [
    { key: "grace", Icon: Waves, cell: cells.grace, signed: true },
    { key: "smap", Icon: Droplets, cell: cells.smap, signed: false },
    { key: "rain", Icon: CloudRain, cell: cells.rain, signed: false },
  ];
  return (
    <section className="water" aria-labelledby="h-water">
      <h2 id="h-water" className="water-title h-title">
        Agua invisible
      </h2>
      <div className="water-cells">
        {items.map(({ key, Icon, cell, signed }) => (
          <div key={key} className="water-cell" data-cell={key}>
            <span className="label">
              <Icon size={16} strokeWidth={1.5} aria-hidden="true" /> {cell.label}
            </span>
            <Figure value={cell.value} signed={signed} className="fig-lg" />
            <small>{cell.limitation}</small>
          </div>
        ))}
      </div>
    </section>
  );
}
