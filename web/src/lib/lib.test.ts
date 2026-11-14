import { describe, expect, it } from "vitest";
import { byRank, orderRows, positions, rankDiff, tableOrder, toRankMap } from "./rankDiff";
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

  it("uses display_order only when a preference is active", () => {
    const display = ["R_SOY_MONO", "R_MAIZE_SOY"]; // R_MAIZE_SOY_COVER missing: goes last
    expect(tableOrder(owner, display, false)).toEqual(["R_MAIZE_SOY", "R_MAIZE_SOY_COVER", "R_SOY_MONO"]);
    expect(tableOrder(owner, display, true)).toEqual(["R_SOY_MONO", "R_MAIZE_SOY", "R_MAIZE_SOY_COVER"]);
    expect(orderRows(owner, display).map((r) => r.rotation_id)).toEqual(["R_SOY_MONO", "R_MAIZE_SOY", "R_MAIZE_SOY_COVER"]);
  });

  it("measures moves on the shown position", () => {
    const before = toRankMap(positions(["A", "B", "C"]));
    expect(rankDiff(before, positions(["C", "A", "B"]))).toEqual({ C: 2, A: -1, B: -1 });
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
