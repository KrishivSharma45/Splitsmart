import { apiClient } from "./client";
import type { Settlement } from "../types";

export interface SettlementCreateInput {
  payer_id: number;
  receiver_id: number;
  amount: string;
  currency?: string;
  date: string;
  note?: string;
}

export async function listSettlements(tripId: number) {
  const { data } = await apiClient.get<Settlement[]>(`/trips/${tripId}/settlements`);
  return data;
}

export async function createSettlement(tripId: number, input: SettlementCreateInput) {
  const { data } = await apiClient.post<Settlement>(`/trips/${tripId}/settlements`, input);
  return data;
}

export async function cancelSettlement(settlementId: number) {
  const { data } = await apiClient.post<Settlement>(`/settlements/${settlementId}/cancel`);
  return data;
}
