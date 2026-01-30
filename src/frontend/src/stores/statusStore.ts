import { create } from 'zustand';

type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'error';
type ActivityState = 'idle' | 'thinking' | 'streaming' | 'processing';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  timestamp: Date;
  duration?: number;
}

interface StatusStore {
  // Connection
  connectionState: ConnectionState;
  lastPing: Date | null;
  latency: number | null;

  // Activity
  activityState: ActivityState;
  activityMessage: string | null;

  // Progress
  progress: {
    active: boolean;
    value: number;
    max: number;
    label: string;
  } | null;

  // Notifications
  notifications: Notification[];

  // Actions
  setConnectionState: (state: ConnectionState) => void;
  updatePing: (latency: number) => void;
  setActivity: (state: ActivityState, message?: string) => void;
  setProgress: (value: number, max: number, label: string) => void;
  clearProgress: () => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  dismissNotification: (id: string) => void;
}

export const useStatusStore = create<StatusStore>((set, get) => ({
  connectionState: 'connecting',
  lastPing: null,
  latency: null,
  activityState: 'idle',
  activityMessage: null,
  progress: null,
  notifications: [],

  setConnectionState: (connectionState) => set({ connectionState }),

  updatePing: (latency) => set({ lastPing: new Date(), latency }),

  setActivity: (activityState, activityMessage) =>
    set({ activityState, activityMessage: activityMessage ?? null }),

  setProgress: (value, max, label) =>
    set({ progress: { active: true, value, max, label } }),

  clearProgress: () => set({ progress: null }),

  addNotification: (notification) => {
    const id = Math.random().toString(36).slice(2);
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
    };
    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto-dismiss
    if (notification.duration !== 0) {
      setTimeout(() => {
        get().dismissNotification(id);
      }, notification.duration || 5000);
    }
  },

  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}));
