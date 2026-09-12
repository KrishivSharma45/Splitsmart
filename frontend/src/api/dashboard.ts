import { apiClient } from "./client";
import type { DashboardSummary } from "../types";

export async function getDashboard() {
  const { data } = await apiClient.get<DashboardSummary>("/dashboard");
  return data;
}
