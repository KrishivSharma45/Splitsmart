import { apiClient } from "./client";
import type { AuditLog, AuditVerifyResponse } from "../types";

export async function listTripAuditLog(tripId: number, eventType?: string) {
  const { data } = await apiClient.get<AuditLog[]>(`/trips/${tripId}/audit`, {
    params: eventType ? { event_type: eventType } : {},
  });
  return data;
}

export async function verifyTripAudit(tripId: number) {
  const { data } = await apiClient.post<AuditVerifyResponse>(`/trips/${tripId}/audit/verify`);
  return data;
}

export async function listMyAuditLog(eventType?: string) {
  const { data } = await apiClient.get<AuditLog[]>("/audit", { params: eventType ? { event_type: eventType } : {} });
  return data;
}

export async function verifyGlobalAudit() {
  const { data } = await apiClient.post<AuditVerifyResponse>("/audit/verify");
  return data;
}
