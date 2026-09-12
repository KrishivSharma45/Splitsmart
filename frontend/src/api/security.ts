import { apiClient } from "./client";
import type { SecurityOverview } from "../types";

export async function getSecurityOverview() {
  const { data } = await apiClient.get<SecurityOverview>("/security/overview");
  return data;
}
