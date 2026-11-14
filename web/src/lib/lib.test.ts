import { describe, expect, it } from "vitest";
import { byRank, rankDiff, toRankMap } from "./rankDiff";
import { formatNumber, formatSigned } from "./format";

describe("rankDiff", () => {
  const tenant = [
    { rotation_id: "R_SOY_MONO", rank: 1 },
    { rotation_id: "R_MAIZE_SOY", rank: 2 },
    { rotation_id: "R_MAIZE_SOY_COVER", rank: 3 },
  ];
  const owner = [
    { rotation_id: "R_MAIZE_SOY", rank: 1 },
    { rotation_id: "R_MAIZE_SOY_COVER", rank: 2 },
    { rotation_id: "R_SOY_MONO", rank: 3 },
  ];

  it("reports +1 for a rotation that moves from 2 to 1", () => {
    const d = rankDiff(toRankMap(tenant), owner);
    expect(d).toEqual({ R_MAIZE_SOY: 1, R_MAIZE_SOY_COVER: 1, R_SOY_MONO: -2 });
  });

  it("reports 0 on the first evaluation and for new rotations", () => {
    expect(rankDiff(null, owner)).toEqual({ R_MAIZE_SOY: 0, R_MAIZE_SOY_COVER: 0, R_SOY_MONO: 0 });
    expect(rankDiff({ R_SOY_MONO: 1 }, [{ rotation_id: "R_NEW", rank: 1 }])).toEqual({ R_NEW: 0 });
  });

  it("orders rows by the engine rank only", () => {
    expect(byRank([...owner].reverse()).map((r) => r.rotation_id)).toEqual(owner.map((r) => r.rotation_id));
  });
});

describe("format (es-AR)", () => {
  it("uses decimal comma and dot thousands", () => {
    expect(formatNumber(0.27, 2)).toBe("0,27");
    expect(formatNumber(1234.5, 1)).toBe("1.234,5");
    expect(formatSigned(-9)).toBe("−9");
    expect(formatSigned(24)).toBe("+24");
  });
});
