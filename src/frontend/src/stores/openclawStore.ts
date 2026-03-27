/**
 * THÉRÈSE v2 - OpenClaw Store
 *
 * State management pour les sessions OpenClaw (US-001).
 * Séparé du atelierStore pour ne pas casser l existant.
 */

import { create } from "zustand";
import type {
  AgentSessionResponse,
  SessionMessageResponse,
  OpenClawStatusResponse,
} from "../services/api/agents";
import {
  dispatchToOpenClaw,
  listOpenClawSessions,
  getOpenClawSession,
  getOpenClawSessionMessages,
  sendToOpenClawSession,
  cancelOpenClawSession,
  getOpenClawStatus,
} from "../services/api/agents";

// ============================================================
// Types
// ============================================================

interface OpenClawState {
  // Connexion
  openclawConnected: boolean;
  openclawAgents: Array<{ id?: string; name?: string; status?: string }>;
  openclawUrl: string;

  // Sessions
  sessions: AgentSessionResponse[];
  sessionsTotal: number;
  activeSessionId: string | null;
  activeSessionMessages: SessionMessageResponse[];

  // Multi-agents (US-003)
  maxAgents: number;
  runningCount: number;

  // UI
  isDispatching: boolean;
  isSending: boolean;
  isNewTaskOpen: boolean;
  error: string | null;

  // Actions - Connexion
  checkOpenClawStatus: () => Promise<void>;

  // Actions - Sessions
  fetchSessions: (limit?: number, status?: string) => Promise<void>;
  dispatchTask: (instruction: string, agentName?: string) => Promise<AgentSessionResponse | null>;
  selectSession: (sessionId: string | null) => void;
  refreshActiveSession: () => Promise<void>;
  fetchSessionMessages: (sessionId: string) => Promise<void>;
  sendMessage: (sessionId: string, content: string) => Promise<void>;
  cancelSession: (sessionId: string) => Promise<void>;

  // Actions - Multi-agents (US-003)
  updateRunningCount: () => void;

  // Actions - UI
  openNewTask: () => void;
  closeNewTask: () => void;
  clearError: () => void;
}

export const useOpenClawStore = create<OpenClawState>((set, get) => ({
  // Initial state
  openclawConnected: false,
  openclawAgents: [],
  openclawUrl: "",
  sessions: [],
  sessionsTotal: 0,
  activeSessionId: null,
  activeSessionMessages: [],
  maxAgents: 3,
  runningCount: 0,
  isDispatching: false,
  isSending: false,
  isNewTaskOpen: false,
  error: null,

  // Connexion
  checkOpenClawStatus: async () => {
    try {
      const status: OpenClawStatusResponse = await getOpenClawStatus();
      set({
        openclawConnected: status.connected,
        openclawAgents: status.agents,
        openclawUrl: status.url,
        error: null,
      });
    } catch (e: any) {
      set({
        openclawConnected: false,
        error: e.message || "Impossible de joindre le backend",
      });
    }
  },

  // Sessions
  fetchSessions: async (limit = 50, status?: string) => {
    try {
      const result = await listOpenClawSessions(limit, status);
      const running = result.sessions.filter((s) => s.status === "running").length;
      set({
        sessions: result.sessions,
        sessionsTotal: result.total,
        runningCount: running,
        error: null,
      });
    } catch (e: any) {
      set({ error: e.message || "Erreur chargement sessions" });
    }
  },

  dispatchTask: async (instruction: string, agentName = "katia") => {
    // US-003 : vérifier la limite côté store
    const { runningCount, maxAgents } = get();
    if (runningCount >= maxAgents) {
      set({ error: `Tu as déjà ${maxAgents} agents en cours. Attends qu'un se termine ou annule-en un.` });
      return null;
    }
    set({ isDispatching: true, error: null });
    try {
      const session = await dispatchToOpenClaw(instruction, agentName);
      // Ajouter la session en tête de liste
      set((s) => ({
        sessions: [session, ...s.sessions],
        sessionsTotal: s.sessionsTotal + 1,
        activeSessionId: session.id,
        activeSessionMessages: [],
        isDispatching: false,
        isNewTaskOpen: false,
        runningCount: s.runningCount + 1,
      }));
      return session;
    } catch (e: any) {
      set({
        isDispatching: false,
        error: e.message || "Erreur lancement agent",
      });
      return null;
    }
  },

  selectSession: (sessionId: string | null) => {
    set({ activeSessionId: sessionId, activeSessionMessages: [] });
    if (sessionId) {
      get().fetchSessionMessages(sessionId);
    }
  },

  refreshActiveSession: async () => {
    const { activeSessionId } = get();
    if (!activeSessionId) return;

    try {
      const session = await getOpenClawSession(activeSessionId);
      set((s) => ({
        sessions: s.sessions.map((sess) =>
          sess.id === activeSessionId ? session : sess
        ),
      }));
      // Rafraichir les messages aussi
      await get().fetchSessionMessages(activeSessionId);
    } catch (e: any) {
      set({ error: e.message || "Erreur rafraichissement" });
    }
  },

  fetchSessionMessages: async (sessionId: string) => {
    try {
      const messages = await getOpenClawSessionMessages(sessionId);
      set({ activeSessionMessages: messages });
    } catch (e: any) {
      // Silencieux - les messages peuvent ne pas encore exister
    }
  },

  sendMessage: async (sessionId: string, content: string) => {
    set({ isSending: true, error: null });
    try {
      await sendToOpenClawSession(sessionId, content);
      // Rafraichir les messages
      await get().fetchSessionMessages(sessionId);
      set({ isSending: false });
    } catch (e: any) {
      set({
        isSending: false,
        error: e.message || "Erreur envoi message",
      });
    }
  },

  cancelSession: async (sessionId: string) => {
    try {
      await cancelOpenClawSession(sessionId);
      set((s) => ({
        sessions: s.sessions.map((sess) =>
          sess.id === sessionId ? { ...sess, status: "cancelled" as const } : sess
        ),
      }));
    } catch (e: any) {
      set({ error: e.message || "Erreur annulation" });
    }
  },

  // Multi-agents (US-003)
  updateRunningCount: () => {
    const { sessions } = get();
    const running = sessions.filter((s) => s.status === "running").length;
    set({ runningCount: running });
  },

  // UI
  openNewTask: () => set({ isNewTaskOpen: true }),
  closeNewTask: () => set({ isNewTaskOpen: false }),
  clearError: () => set({ error: null }),
}));
