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

/** Rows in a given id order (the API's `display_order`); ids it does not list go last, by rank. */
export function orderRows<T extends Ranked>(results: readonly T[], order: readonly string[]): T[] {
  const byId = new Map(results.map((r) => [r.rotation_id, r]));
  const listed = order.flatMap((id) => (byId.has(id) ? [byId.get(id)!] : []));
  const seen = new Set(listed.map((r) => r.rotation_id));
  return [...listed, ...byRank(results.filter((r) => !seen.has(r.rotation_id)))];
}

/** Which order the table shows: the API's `display_order` when a preference is active, else `rank`. */
export const tableOrder = (results: readonly Ranked[], displayOrder: readonly string[], preferencesActive: boolean): string[] =>
  preferencesActive && displayOrder.length ? orderRows(results, displayOrder).map((r) => r.rotation_id) : byRank(results).map((r) => r.rotation_id);

/** Shown position (1-based) of each row, in the shape `rankDiff` reads. */
export const positions = (order: readonly string[]): Ranked[] => order.map((rotation_id, i) => ({ rotation_id, rank: i + 1 }));
