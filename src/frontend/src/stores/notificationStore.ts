/**
 * THERESE v2 - Notification Store (US-004)
 *
 * Store Zustand pour les notifications push in-app.
 * Polling du count toutes les 60 secondes.
 */

import { create } from "zustand";
import {
  listNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
  type AppNotification,
} from "../services/api/notifications";

interface NotificationState {
  notifications: AppNotification[];
  unreadCount: number;
  isOpen: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchNotifications: () => Promise<void>;
  fetchUnreadCount: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllRead: () => Promise<void>;
  toggle: () => void;
  close: () => void;

  // Polling
  startPolling: () => void;
  stopPolling: () => void;
}

let pollingInterval: ReturnType<typeof setInterval> | null = null;

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isOpen: false,
  isLoading: false,
  error: null,

  fetchNotifications: async () => {
    set({ isLoading: true, error: null });
    try {
      const notifications = await listNotifications({ limit: 50 });
      set({ notifications, isLoading: false });
    } catch (e: any) {
      set({ error: e.message, isLoading: false });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const data = await getUnreadCount();
      set({ unreadCount: data.unread_count });
    } catch {
      // Silencieux - le polling ne doit pas spammer les erreurs
    }
  },

  markAsRead: async (id: string) => {
    try {
      await markNotificationRead(id);
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch (e: any) {
      console.error("Erreur markAsRead:", e);
    }
  },

  markAllRead: async () => {
    try {
      await markAllNotificationsRead();
      set((state) => ({
        notifications: state.notifications.map((n) => ({
          ...n,
          is_read: true,
          read_at: n.read_at || new Date().toISOString(),
        })),
        unreadCount: 0,
      }));
    } catch (e: any) {
      console.error("Erreur markAllRead:", e);
    }
  },

  toggle: () => {
    const isOpen = !get().isOpen;
    set({ isOpen });
    if (isOpen) {
      // Charger les notifications quand on ouvre le panneau
      get().fetchNotifications();
    }
  },

  close: () => set({ isOpen: false }),

  startPolling: () => {
    // Fetch initial
    get().fetchUnreadCount();

    // Polling toutes les 60 secondes
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(() => {
      get().fetchUnreadCount();
    }, 60_000);
  },

  stopPolling: () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  },
}));
