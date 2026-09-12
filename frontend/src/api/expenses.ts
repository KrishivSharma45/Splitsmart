import { apiClient } from "./client";
import type { Expense, ExpenseCategory, ExpenseParticipantInput, ExpenseStatus, SplitMethod } from "../types";

export interface ExpenseCreateInput {
  description: string;
  amount: string;
  currency?: string;
  paid_by: number;
  category: ExpenseCategory;
  split_method: SplitMethod;
  date: string;
  notes?: string;
  participants: ExpenseParticipantInput[];
}

export interface ExpenseFilters {
  category?: ExpenseCategory;
  paid_by?: number;
  participant?: number;
  date_from?: string;
  date_to?: string;
  amount_min?: string;
  amount_max?: string;
  search?: string;
  status?: ExpenseStatus;
  sort_by?: "date" | "amount" | "category" | "created_at";
  sort_dir?: "asc" | "desc";
}

export async function listExpenses(tripId: number, filters: ExpenseFilters = {}) {
  const { data } = await apiClient.get<Expense[]>(`/trips/${tripId}/expenses`, { params: filters });
  return data;
}

export async function createExpense(tripId: number, input: ExpenseCreateInput) {
  const { data } = await apiClient.post<Expense>(`/trips/${tripId}/expenses`, input);
  return data;
}

export async function getExpense(expenseId: number) {
  const { data } = await apiClient.get<Expense>(`/expenses/${expenseId}`);
  return data;
}

export async function updateExpense(expenseId: number, input: Partial<ExpenseCreateInput>) {
  const { data } = await apiClient.put<Expense>(`/expenses/${expenseId}`, input);
  return data;
}

export async function voidExpense(expenseId: number, reason?: string) {
  const { data } = await apiClient.post<Expense>(`/expenses/${expenseId}/void`, { reason });
  return data;
}

export async function uploadReceipt(expenseId: number, file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post(`/expenses/${expenseId}/receipt`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function downloadReceipt(expenseId: number) {
  const response = await apiClient.get(`/expenses/${expenseId}/receipt`, { responseType: "blob" });
  const disposition = response.headers["content-disposition"] as string | undefined;
  const match = disposition?.match(/filename="?([^"]+)"?/);
  const filename = match?.[1] ?? `receipt-${expenseId}`;

  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
