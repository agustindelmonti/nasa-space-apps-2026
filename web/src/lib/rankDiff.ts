// Presentation-only comparison between two rankings delivered by the engine. It never
// recalculates scores or reorders: it only reads `rank`.
export interface Ranked {
  rotation_id: string;
  rank: number;
}

export type RankMap = Record<string, number>;

export const toRankMap = (results: readonly Ranked[]): RankMap =>
  Object.fromEntries(results.map((r) => [r.rotation_id, r.rank]));

/** Positions moved since the previous ranking: +n moved up, −n moved down, 0 same or new. */
export function rankDiff(previous: RankMap | null, current: readonly Ranked[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const r of current) {
    const before = previous?.[r.rotation_id];
    out[r.rotation_id] = before === undefined ? 0 : before - r.rank;
  }
  return out;
}

/** Rows in the order the engine ranked them (by `rank`, never by score). */
export const byRank = <T extends Ranked>(results: readonly T[]): T[] => [...results].sort((a, b) => a.rank - b.rank);
