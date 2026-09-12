import { apiClient } from "./client";
import type { Notification } from "../types";

export async function listNotifications(unreadOnly = false) {
  const { data } = await apiClient.get<Notification[]>("/notifications", { params: { unread_only: unreadOnly } });
  return data;
}

export async function markRead(notificationId: number) {
  const { data } = await apiClient.patch<Notification>(`/notifications/${notificationId}/read`);
  return data;
}

export async function markAllRead() {
  await apiClient.post("/notifications/read-all");
}
