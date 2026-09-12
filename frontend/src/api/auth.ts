import { apiClient } from "./client";
import type { User } from "../types";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function register(email: string, full_name: string, password: string) {
  const { data } = await apiClient.post<TokenResponse>("/auth/register", { email, full_name, password });
  return data;
}

export async function login(email: string, password: string) {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", { email, password });
  return data;
}

export async function refresh() {
  const { data } = await apiClient.post<TokenResponse>("/auth/refresh");
  return data;
}

export async function logout() {
  await apiClient.post("/auth/logout");
}

export async function getMe() {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}

export async function updateMe(full_name: string) {
  const { data } = await apiClient.patch<User>("/auth/me", { full_name });
  return data;
}

export async function changePassword(current_password: string, new_password: string) {
  await apiClient.post("/auth/change-password", { current_password, new_password });
}
