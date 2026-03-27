/**
 * THÉRÈSE v2 - Panel Store (US-016)
 *
 * Store Zustand pour la gestion centralisée des panneaux latéraux et modaux.
 * Remplace les 20+ useState de ChatLayout.tsx.
 */

import { create } from 'zustand';
import * as api from '../services/api';

// ============================================================
// Types
// ============================================================

export type PanelId =
  | 'memory'
  | 'board'
  | 'settings'
  | 'atelier'
  | 'contacts'
  | 'projects'
  | 'commandPalette'
  | 'shortcuts'
  | 'conversationSidebar'
  | 'saveCommand';

interface SaveCommandData {
  userPrompt: string;
  assistantContent: string;
}

interface PanelState {
  // Panels ouverts/fermés
  activePanel: PanelId | null;
  showConversationSidebar: boolean;
  showCommandPalette: boolean;
  showShortcuts: boolean;
  showSettings: boolean;
  showMemoryPanel: boolean;
  showBoardPanel: boolean;
  showContactModal: boolean;
  showProjectModal: boolean;
  showSaveCommand: boolean;

  // Données contextuelles
  editingContact: api.Contact | null;
  editingProject: api.Project | null;
  saveCommandData: SaveCommandData | null;

  // Actions panneaux
  setActivePanel: (panel: PanelId | null) => void;
  togglePanel: (panel: PanelId) => void;
  closePanel: (panel: PanelId) => void;
  closeAll: () => void;

  // Actions spécifiques (pour éviter les dépendances circulaires)
  openCommandPalette: () => void;
  closeCommandPalette: () => void;
  openShortcuts: () => void;
  closeShortcuts: () => void;
  openSettings: () => void;
  closeSettings: () => void;
  toggleMemoryPanel: () => void;
  closeMemoryPanel: () => void;
  toggleBoardPanel: () => void;
  closeBoardPanel: () => void;
  toggleConversationSidebar: () => void;
  closeConversationSidebar: () => void;

  // Contacts
  openNewContact: () => void;
  openEditContact: (contact: api.Contact) => void;
  closeContactModal: () => void;

  // Projects
  openNewProject: () => void;
  closeProjectModal: () => void;

  // Save Command
  openSaveCommand: (userPrompt: string, assistantContent: string) => void;
  closeSaveCommand: () => void;

  // Escape handler : ferme le panel le plus en avant
  handleEscape: () => void;
}

// ============================================================
// Store
// ============================================================

export const usePanelStore = create<PanelState>((set, get) => ({
  // État initial
  activePanel: null,
  showConversationSidebar: true,
  showCommandPalette: false,
  showShortcuts: false,
  showSettings: false,
  showMemoryPanel: false,
  showBoardPanel: false,
  showContactModal: false,
  showProjectModal: false,
  showSaveCommand: false,

  editingContact: null,
  editingProject: null,
  saveCommandData: null,

  // Actions génériques
  setActivePanel: (panel) => set({ activePanel: panel }),

  togglePanel: (panel) => {
    const state = get();
    const mapping: Record<string, keyof PanelState> = {
      memory: 'showMemoryPanel',
      board: 'showBoardPanel',
      settings: 'showSettings',
      commandPalette: 'showCommandPalette',
      shortcuts: 'showShortcuts',
      conversationSidebar: 'showConversationSidebar',
    };
    const key = mapping[panel];
    if (key) {
      set({ [key]: !state[key] } as Partial<PanelState>);
    }
  },

  closePanel: (panel) => {
    const mapping: Record<string, keyof PanelState> = {
      memory: 'showMemoryPanel',
      board: 'showBoardPanel',
      settings: 'showSettings',
      commandPalette: 'showCommandPalette',
      shortcuts: 'showShortcuts',
      conversationSidebar: 'showConversationSidebar',
      contacts: 'showContactModal',
      projects: 'showProjectModal',
      saveCommand: 'showSaveCommand',
    };
    const key = mapping[panel];
    if (key) {
      set({ [key]: false } as Partial<PanelState>);
    }
  },

  closeAll: () =>
    set({
      showCommandPalette: false,
      showShortcuts: false,
      showSettings: false,
      showMemoryPanel: false,
      showBoardPanel: false,
      showContactModal: false,
      showProjectModal: false,
      showSaveCommand: false,
      editingContact: null,
      editingProject: null,
      saveCommandData: null,
    }),

  // Actions spécifiques
  openCommandPalette: () => set({ showCommandPalette: true }),
  closeCommandPalette: () => set({ showCommandPalette: false }),
  openShortcuts: () => set({ showShortcuts: true }),
  closeShortcuts: () => set({ showShortcuts: false }),
  openSettings: () => set({ showSettings: true }),
  closeSettings: () => set({ showSettings: false }),
  toggleMemoryPanel: () => set((s) => ({ showMemoryPanel: !s.showMemoryPanel })),
  closeMemoryPanel: () => set({ showMemoryPanel: false }),
  toggleBoardPanel: () => set((s) => ({ showBoardPanel: !s.showBoardPanel })),
  closeBoardPanel: () => set({ showBoardPanel: false }),
  toggleConversationSidebar: () =>
    set((s) => ({ showConversationSidebar: !s.showConversationSidebar })),
  closeConversationSidebar: () => set({ showConversationSidebar: false }),

  // Contacts
  openNewContact: () => set({ editingContact: null, showContactModal: true }),
  openEditContact: (contact) => set({ editingContact: contact, showContactModal: true }),
  closeContactModal: () => set({ showContactModal: false, editingContact: null }),

  // Projects
  openNewProject: () => set({ editingProject: null, showProjectModal: true }),
  closeProjectModal: () => set({ showProjectModal: false, editingProject: null }),

  // Save Command
  openSaveCommand: (userPrompt, assistantContent) =>
    set({
      showSaveCommand: true,
      saveCommandData: { userPrompt, assistantContent },
    }),
  closeSaveCommand: () =>
    set({
      showSaveCommand: false,
      saveCommandData: null,
    }),

  // Escape : ferme le modal le plus en avant (z-index décroissant)
  handleEscape: () => {
    const s = get();
    if (s.showBoardPanel) {
      set({ showBoardPanel: false });
    } else if (s.showContactModal) {
      set({ showContactModal: false, editingContact: null });
    } else if (s.showProjectModal) {
      set({ showProjectModal: false, editingProject: null });
    } else if (s.showCommandPalette) {
      set({ showCommandPalette: false });
    } else if (s.showShortcuts) {
      set({ showShortcuts: false });
    } else if (s.showSettings) {
      set({ showSettings: false });
    } else if (s.showMemoryPanel) {
      set({ showMemoryPanel: false });
    } else if (s.showConversationSidebar) {
      set({ showConversationSidebar: false });
    }
  },
}));
