/**
 * THÉRÈSE v2 - Atelier Store
 *
 * State management pour le panneau Atelier (agents Katia & Zézette).
 * Pattern Zustand identique à chatStore.ts.
 */

import { create } from 'zustand';
import type { AgentId, AgentStreamChunk, MissionPhase } from '../services/api/agents';

// ============================================================
// Types
// ============================================================

export interface AgentMessage {
  id: string;
  agentId: AgentId | 'user' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  type?: 'normal' | 'handoff' | 'tool_use' | 'test_result' | 'explanation';
  toolName?: string;
}

export interface Mission {
  id: string;
  taskId: string;
  summary: string;
  phase: MissionPhase;
  branch?: string;
  filesChanged?: string[];
  diffSummary?: string;
  explanation?: string;
  startedAt: Date;
  completedAt?: Date;
  error?: string;
}

export type AtelierView = 'chat' | 'mission' | 'review' | 'openclaw';

// ============================================================
// Store
// ============================================================

interface AtelierState {
  // Panel
  isOpen: boolean;
  activeView: AtelierView;

  // Chat
  messages: AgentMessage[];
  isStreaming: boolean;
  currentStreamingId: string | null;

  // Mission
  currentMission: Mission | null;
  missionHistory: Mission[];

  // Config
  sourcePath: string | null;

  // Actions - Panel
  togglePanel: () => void;
  openPanel: () => void;
  closePanel: () => void;
  setActiveView: (view: AtelierView) => void;

  // Actions - Chat
  addUserMessage: (content: string) => string;
  startAgentStream: (agentId: AgentId) => string;
  appendToStream: (messageId: string, content: string) => void;
  endStream: (messageId: string) => void;
  addSystemMessage: (content: string, type?: AgentMessage['type'], toolName?: string) => void;
  clearMessages: () => void;

  // Actions - Mission
  startMission: (taskId: string, summary: string) => void;
  updateMissionPhase: (phase: MissionPhase) => void;
  setMissionBranch: (branch: string, files?: string[], diffSummary?: string) => void;
  setMissionExplanation: (explanation: string) => void;
  completeMission: () => void;
  failMission: (error: string) => void;

  // Actions - Config
  setSourcePath: (path: string) => void;

  // Actions - Process SSE chunk
  processChunk: (chunk: AgentStreamChunk) => void;
}

let _messageCounter = 0;
function generateId(): string {
  return `msg-${Date.now()}-${++_messageCounter}`;
}

export const useAtelierStore = create<AtelierState>((set, get) => ({
  // Initial state
  isOpen: false,
  activeView: 'chat',
  messages: [],
  isStreaming: false,
  currentStreamingId: null,
  currentMission: null,
  missionHistory: [],
  sourcePath: null,

  // Panel
  togglePanel: () => set((s) => ({ isOpen: !s.isOpen })),
  openPanel: () => set({ isOpen: true }),
  closePanel: () => set({ isOpen: false }),
  setActiveView: (view) => set({ activeView: view }),

  // Chat
  addUserMessage: (content) => {
    const id = generateId();
    set((s) => ({
      messages: [...s.messages, {
        id,
        agentId: 'user',
        content,
        timestamp: new Date(),
      }],
    }));
    return id;
  },

  startAgentStream: (agentId) => {
    const id = generateId();
    set((s) => ({
      messages: [...s.messages, {
        id,
        agentId,
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      }],
      isStreaming: true,
      currentStreamingId: id,
    }));
    return id;
  },

  appendToStream: (messageId, content) => {
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === messageId ? { ...m, content: m.content + content } : m
      ),
    }));
  },

  endStream: (messageId) => {
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === messageId ? { ...m, isStreaming: false } : m
      ),
      isStreaming: false,
      currentStreamingId: null,
    }));
  },

  addSystemMessage: (content, type = 'normal', toolName) => {
    set((s) => ({
      messages: [...s.messages, {
        id: generateId(),
        agentId: 'system',
        content,
        timestamp: new Date(),
        type,
        toolName,
      }],
    }));
  },

  clearMessages: () => set({ messages: [], currentStreamingId: null, isStreaming: false }),

  // Mission
  startMission: (taskId, summary) => {
    const mission: Mission = {
      id: generateId(),
      taskId,
      summary,
      phase: 'spec',
      startedAt: new Date(),
    };
    set({ currentMission: mission, activeView: 'mission' });
  },

  updateMissionPhase: (phase) => {
    set((s) => ({
      currentMission: s.currentMission
        ? { ...s.currentMission, phase }
        : null,
    }));
  },

  setMissionBranch: (branch, files, diffSummary) => {
    set((s) => ({
      currentMission: s.currentMission
        ? { ...s.currentMission, branch, filesChanged: files, diffSummary }
        : null,
    }));
  },

  setMissionExplanation: (explanation) => {
    set((s) => ({
      currentMission: s.currentMission
        ? { ...s.currentMission, explanation }
        : null,
    }));
  },

  completeMission: () => {
    set((s) => {
      if (!s.currentMission) return s;
      const completed = { ...s.currentMission, phase: 'done' as MissionPhase, completedAt: new Date() };
      return {
        currentMission: completed,
        missionHistory: [completed, ...s.missionHistory],
        activeView: 'review',
      };
    });
  },

  failMission: (error) => {
    set((s) => ({
      currentMission: s.currentMission
        ? { ...s.currentMission, error, phase: 'done' as MissionPhase }
        : null,
    }));
  },

  // Config
  setSourcePath: (path) => set({ sourcePath: path }),

  // Process SSE chunk - central handler
  processChunk: (chunk) => {
    const state = get();

    switch (chunk.type) {
      case 'agent_start': {
        const agentId = chunk.agent || 'katia';
        state.startAgentStream(agentId);
        if (chunk.phase) state.updateMissionPhase(chunk.phase);
        break;
      }

      case 'agent_chunk': {
        if (state.currentStreamingId) {
          state.appendToStream(state.currentStreamingId, chunk.content);
        }
        break;
      }

      case 'agent_done': {
        if (state.currentStreamingId) {
          state.endStream(state.currentStreamingId);
        }
        break;
      }

      case 'handoff': {
        state.addSystemMessage(
          chunk.content,
          'handoff',
        );
        if (chunk.task_id && !state.currentMission) {
          state.startMission(chunk.task_id, chunk.content.slice(0, 100));
        }
        break;
      }

      case 'tool_use': {
        state.addSystemMessage(
          `Utilisation de ${chunk.tool_name || 'outil'}...`,
          'tool_use',
          chunk.tool_name || undefined,
        );
        break;
      }

      case 'test_result': {
        state.addSystemMessage(chunk.content, 'test_result');
        break;
      }

      case 'review_ready': {
        if (chunk.branch) {
          state.setMissionBranch(
            chunk.branch,
            chunk.files_changed,
            chunk.diff_summary,
          );
        }
        state.updateMissionPhase('review');
        break;
      }

      case 'explanation': {
        if (state.currentStreamingId) {
          state.appendToStream(state.currentStreamingId, chunk.content);
        }
        if (chunk.content) {
          state.setMissionExplanation(chunk.content);
        }
        break;
      }

      case 'done': {
        if (state.currentStreamingId) {
          state.endStream(state.currentStreamingId);
        }
        if (chunk.phase === 'review') {
          state.completeMission();
        }
        break;
      }

      case 'error': {
        if (state.currentStreamingId) {
          state.endStream(state.currentStreamingId);
        }
        state.addSystemMessage(chunk.content, 'normal');
        if (state.currentMission) {
          state.failMission(chunk.content);
        }
        break;
      }
    }
  },
}));
