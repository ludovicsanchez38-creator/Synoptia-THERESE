/**
 * THERESE v2 - Notifications API Module (US-004)
 *
 * Gestion des notifications push in-app.
 */

import { API_BASE, apiFetch } from "./core";

export interface AppNotification {
  id: string;
  title: string;
  message: string;
  type: "info" | "warning" | "action" | "reminder";
  source: "crm" | "invoice" | "calendar" | "task" | "agent" | "system";
  action_url: string | null;
  action_label: string | null;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}

export interface NotificationCount {
  unread_count: number;
}

export async function listNotifications(params?: {
  limit?: number;
  unread_only?: boolean;
}): Promise<AppNotification[]> {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.set("limit", String(params.limit));
  if (params?.unread_only) queryParams.set("unread_only", "true");

  const response = await apiFetch(
    `${API_BASE}/api/notifications?${queryParams}`
  );
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(d.detail || d.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function getUnreadCount(): Promise<NotificationCount> {
  const response = await apiFetch(`${API_BASE}/api/notifications/count`);
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(d.detail || d.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function markNotificationRead(
  notificationId: string
): Promise<AppNotification> {
  const response = await apiFetch(
    `${API_BASE}/api/notifications/${notificationId}/read`,
    { method: "PATCH" }
  );
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(d.detail || d.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function markAllNotificationsRead(): Promise<{
  marked_read: number;
}> {
  const response = await apiFetch(`${API_BASE}/api/notifications/read-all`, {
    method: "POST",
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(d.detail || d.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function generateNotifications(): Promise<{
  generated: Record<string, number>;
  total: number;
}> {
  const response = await apiFetch(`${API_BASE}/api/notifications/generate`, {
    method: "POST",
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(d.detail || d.message || `Erreur ${response.status}`);
  }
  return response.json();
}
