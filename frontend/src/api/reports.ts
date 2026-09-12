import { apiClient, getAccessToken } from "./client";
import type { ReportSummary } from "../types";

export async function getReportSummary(tripId: number) {
  const { data } = await apiClient.get<ReportSummary>(`/reports/${tripId}`);
  return data;
}

function withBase(path: string) {
  const base = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
  return `${base}${path}`;
}

export async function downloadExport(url: string, filename: string) {
  const response = await fetch(withBase(url), {
    headers: { Authorization: `Bearer ${getAccessToken() ?? ""}` },
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Failed to generate export");
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

export function csvExportUrl(tripId: number, type: "expenses" | "balances" | "settlements" | "audit") {
  return `/reports/${tripId}/export/csv?type=${type}`;
}

export function pdfExportUrl(tripId: number) {
  return `/reports/${tripId}/export/pdf`;
}
