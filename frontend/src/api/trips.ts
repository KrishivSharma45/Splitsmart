import { apiClient } from "./client";
import type {
  BalancesResponse,
  DebtsResponse,
  Trip,
  TripListItem,
  TripMember,
  TripRole,
} from "../types";

export interface TripCreateInput {
  name: string;
  description?: string;
  destination?: string;
  start_date?: string;
  end_date?: string;
  currency?: string;
}

export async function listTrips() {
  const { data } = await apiClient.get<TripListItem[]>("/trips");
  return data;
}

export async function createTrip(input: TripCreateInput) {
  const { data } = await apiClient.post<Trip>("/trips", input);
  return data;
}

export async function getTrip(tripId: number) {
  const { data } = await apiClient.get<Trip>(`/trips/${tripId}`);
  return data;
}

export async function updateTrip(tripId: number, input: Partial<TripCreateInput>) {
  const { data } = await apiClient.put<Trip>(`/trips/${tripId}`, input);
  return data;
}

export async function archiveTrip(tripId: number) {
  const { data } = await apiClient.delete<Trip>(`/trips/${tripId}`);
  return data;
}

export async function listMembers(tripId: number) {
  const { data } = await apiClient.get<TripMember[]>(`/trips/${tripId}/members`);
  return data;
}

export async function addMember(tripId: number, email: string, role: TripRole = "MEMBER") {
  const { data } = await apiClient.post<TripMember>(`/trips/${tripId}/members`, { email, role });
  return data;
}

export async function removeMember(tripId: number, userId: number) {
  await apiClient.delete(`/trips/${tripId}/members/${userId}`);
}

export async function changeMemberRole(tripId: number, userId: number, role: TripRole) {
  const { data } = await apiClient.patch<TripMember>(`/trips/${tripId}/members/${userId}`, { role });
  return data;
}

export async function getBalances(tripId: number) {
  const { data } = await apiClient.get<BalancesResponse>(`/trips/${tripId}/balances`);
  return data;
}

export async function getDebts(tripId: number) {
  const { data } = await apiClient.get<DebtsResponse>(`/trips/${tripId}/debts`);
  return data;
}
