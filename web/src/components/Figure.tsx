import type { PValue } from "../data/types";
import { digitsFor, formatNumber, formatSigned, unitLabel } from "../lib/format";
import { ProvenanceBadge } from "./ProvenanceBadge";

interface Props {
  value: PValue;
  signed?: boolean;
  badge?: boolean;
  className?: string;
}

/** A number with its unit (Figure style) and, optionally, its provenance badge. */
export function Figure({ value, signed, badge = true, className = "" }: Props) {
  const d = digitsFor(value.unit, value.value);
  const unit = unitLabel(value.unit);
  return (
    <span className={`figwrap ${className}`}>
      <span className="fig">
        {signed ? formatSigned(value.value, d) : formatNumber(value.value, d)}
        {unit && <span className="unit"> {unit}</span>}
      </span>
      {badge && <ProvenanceBadge provenance={value.provenance} />}
    </span>
  );
}
