import type { TripRole } from "../types";

const RANK: Record<TripRole, number> = { MEMBER: 0, ADMIN: 1, OWNER: 2 };

export function isAtLeast(role: TripRole | null | undefined, minimum: TripRole) {
  if (!role) return false;
  return RANK[role] >= RANK[minimum];
}
