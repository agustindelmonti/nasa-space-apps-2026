import { CircleCheck, CircleHelp, CircleX, TriangleAlert } from "lucide-react";
import type { WaterFeasibility } from "../data/types";
import { WATER_LABEL } from "../lib/labels";

const ICON = { FEASIBLE: CircleCheck, RISKY: TriangleAlert, NOT_FEASIBLE: CircleX, UNKNOWN: CircleHelp };
const CLS = { FEASIBLE: "st-feasible", RISKY: "st-risky", NOT_FEASIBLE: "st-not-feasible", UNKNOWN: "st-unknown" };

/** Water state: icon + word, never color alone. */
export function WaterState({ state }: { state: WaterFeasibility }) {
  const Icon = ICON[state];
  return (
    <span className={`state ${CLS[state]}`}>
      <Icon size={16} strokeWidth={1.5} aria-hidden="true" />
      <span className="state-word">{WATER_LABEL[state]}</span>
    </span>
  );
}
