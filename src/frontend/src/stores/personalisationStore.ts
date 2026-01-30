/**
 * THERESE v2 - Personalisation Store
 *
 * Store for managing user personalisation preferences.
 * US-PERS-01 to US-PERS-05
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ============================================================
// US-PERS-01: Custom Keyboard Shortcuts
// ============================================================

export interface KeyboardShortcut {
  action: string;
  key: string;
  modifiers: ('cmd' | 'ctrl' | 'alt' | 'shift')[];
  description: string;
}

const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  { action: 'newConversation', key: 'N', modifiers: ['cmd'], description: 'Nouvelle conversation' },
  { action: 'toggleSidebar', key: 'B', modifiers: ['cmd'], description: 'Afficher/masquer conversations' },
  { action: 'toggleMemory', key: 'M', modifiers: ['cmd'], description: 'Afficher/masquer espace de travail' },
  { action: 'toggleBoard', key: 'D', modifiers: ['cmd'], description: 'Board de decision' },
  { action: 'commandPalette', key: 'K', modifiers: ['cmd'], description: 'Palette de commandes' },
  { action: 'focusInput', key: '/', modifiers: [], description: 'Focus sur le chat' },
  { action: 'clearChat', key: 'L', modifiers: ['cmd', 'shift'], description: 'Effacer conversation' },
  { action: 'settings', key: ',', modifiers: ['cmd'], description: 'Parametres' },
  { action: 'newContact', key: 'C', modifiers: ['cmd', 'shift'], description: 'Nouveau contact' },
  { action: 'newProject', key: 'P', modifiers: ['cmd', 'shift'], description: 'Nouveau projet' },
];

// ============================================================
// US-PERS-02: Custom Prompt Templates
// ============================================================

export interface PromptTemplate {
  id: string;
  name: string;
  prompt: string;
  category: string;
  icon?: string;
  createdAt: Date;
}

// ============================================================
// US-PERS-04: LLM Behavior Defaults
// ============================================================

export interface LLMBehavior {
  // System prompt customization
  customSystemPrompt: string;
  useCustomSystemPrompt: boolean;

  // Response style
  responseStyle: 'concise' | 'detailed' | 'creative';
  language: 'french' | 'english' | 'auto';

  // Context settings
  includeMemoryContext: boolean;
  maxHistoryMessages: number;
}

const DEFAULT_LLM_BEHAVIOR: LLMBehavior = {
  customSystemPrompt: '',
  useCustomSystemPrompt: false,
  responseStyle: 'detailed',
  language: 'french',
  includeMemoryContext: true,
  maxHistoryMessages: 50,
};

// ============================================================
// US-PERS-05: Feature Visibility
// ============================================================

export interface FeatureVisibility {
  showBoard: boolean;
  showCalculators: boolean;
  showImageGeneration: boolean;
  showVoiceInput: boolean;
  showFileBrowser: boolean;
  showMCPTools: boolean;
  showGuidedPrompts: boolean;
  showEntitySuggestions: boolean;
}

const DEFAULT_FEATURE_VISIBILITY: FeatureVisibility = {
  showBoard: true,
  showCalculators: true,
  showImageGeneration: true,
  showVoiceInput: true,
  showFileBrowser: true,
  showMCPTools: true,
  showGuidedPrompts: true,
  showEntitySuggestions: true,
};

// ============================================================
// Store Interface
// ============================================================

interface PersonalisationState {
  // US-PERS-01: Keyboard shortcuts
  shortcuts: KeyboardShortcut[];
  setShortcut: (action: string, key: string, modifiers: ('cmd' | 'ctrl' | 'alt' | 'shift')[]) => void;
  resetShortcuts: () => void;
  getShortcutForAction: (action: string) => KeyboardShortcut | undefined;

  // US-PERS-02: Prompt templates
  promptTemplates: PromptTemplate[];
  addPromptTemplate: (template: Omit<PromptTemplate, 'id' | 'createdAt'>) => void;
  removePromptTemplate: (id: string) => void;
  updatePromptTemplate: (id: string, updates: Partial<Omit<PromptTemplate, 'id' | 'createdAt'>>) => void;

  // US-PERS-04: LLM behavior
  llmBehavior: LLMBehavior;
  setLLMBehavior: (behavior: Partial<LLMBehavior>) => void;
  resetLLMBehavior: () => void;

  // US-PERS-05: Feature visibility
  featureVisibility: FeatureVisibility;
  setFeatureVisibility: (visibility: Partial<FeatureVisibility>) => void;
  resetFeatureVisibility: () => void;
}

export const usePersonalisationStore = create<PersonalisationState>()(
  persist(
    (set, get) => ({
      // ============================================================
      // US-PERS-01: Keyboard Shortcuts
      // ============================================================

      shortcuts: DEFAULT_SHORTCUTS,

      setShortcut: (action, key, modifiers) => {
        set((state) => ({
          shortcuts: state.shortcuts.map((s) =>
            s.action === action ? { ...s, key, modifiers } : s
          ),
        }));
      },

      resetShortcuts: () => set({ shortcuts: DEFAULT_SHORTCUTS }),

      getShortcutForAction: (action) => {
        return get().shortcuts.find((s) => s.action === action);
      },

      // ============================================================
      // US-PERS-02: Prompt Templates
      // ============================================================

      promptTemplates: [],

      addPromptTemplate: (template) => {
        const newTemplate: PromptTemplate = {
          ...template,
          id: crypto.randomUUID(),
          createdAt: new Date(),
        };
        set((state) => ({
          promptTemplates: [...state.promptTemplates, newTemplate],
        }));
      },

      removePromptTemplate: (id) => {
        set((state) => ({
          promptTemplates: state.promptTemplates.filter((t) => t.id !== id),
        }));
      },

      updatePromptTemplate: (id, updates) => {
        set((state) => ({
          promptTemplates: state.promptTemplates.map((t) =>
            t.id === id ? { ...t, ...updates } : t
          ),
        }));
      },

      // ============================================================
      // US-PERS-04: LLM Behavior
      // ============================================================

      llmBehavior: DEFAULT_LLM_BEHAVIOR,

      setLLMBehavior: (behavior) => {
        set((state) => ({
          llmBehavior: { ...state.llmBehavior, ...behavior },
        }));
      },

      resetLLMBehavior: () => set({ llmBehavior: DEFAULT_LLM_BEHAVIOR }),

      // ============================================================
      // US-PERS-05: Feature Visibility
      // ============================================================

      featureVisibility: DEFAULT_FEATURE_VISIBILITY,

      setFeatureVisibility: (visibility) => {
        set((state) => ({
          featureVisibility: { ...state.featureVisibility, ...visibility },
        }));
      },

      resetFeatureVisibility: () => set({ featureVisibility: DEFAULT_FEATURE_VISIBILITY }),
    }),
    {
      name: 'therese-personalisation',
    }
  )
);

/**
 * Hook to format a shortcut for display.
 */
export function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];

  if (shortcut.modifiers.includes('cmd')) parts.push('⌘');
  if (shortcut.modifiers.includes('ctrl')) parts.push('⌃');
  if (shortcut.modifiers.includes('alt')) parts.push('⌥');
  if (shortcut.modifiers.includes('shift')) parts.push('⇧');

  parts.push(shortcut.key.toUpperCase());

  return parts.join('');
}

/**
 * Check if an event matches a shortcut.
 */
export function matchesShortcut(event: KeyboardEvent, shortcut: KeyboardShortcut): boolean {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const cmdKey = isMac ? event.metaKey : event.ctrlKey;

  const modifiersMatch =
    (shortcut.modifiers.includes('cmd') === cmdKey) &&
    (shortcut.modifiers.includes('shift') === event.shiftKey) &&
    (shortcut.modifiers.includes('alt') === event.altKey);

  const keyMatch = event.key.toUpperCase() === shortcut.key.toUpperCase();

  return modifiersMatch && keyMatch;
}
