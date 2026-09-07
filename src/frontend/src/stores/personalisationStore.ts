/**
 * THERESE v2 - Personalisation Store
 *
 * Store for managing user personalisation preferences.
 * US-PERS-01 to US-PERS-05
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';


// ============================================================
// US-PERS-06: UX Mode (Standard / Contributeur)
// ============================================================

export type UXMode = 'standard' | 'contributeur';
const DEFAULT_UX_MODE: UXMode = 'standard';

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

/**
 * B-095 : `showGuidedPrompts` a été retiré d'ici. Les invites guidées ont
 * disparu avec `GuidedPrompts` (B-094) ; le réglage qui les commandait est
 * resté déclaré, sans plus aucun lecteur. Un interrupteur dont le fil a été
 * coupé vaut moins que pas d'interrupteur du tout.
 */
export interface FeatureVisibility {
  showBoard: boolean;
  showCalculators: boolean;
  showImageGeneration: boolean;
  showVoiceInput: boolean;
  showFileBrowser: boolean;
  showMCPTools: boolean;
  showEntitySuggestions: boolean;
}

const DEFAULT_FEATURE_VISIBILITY: FeatureVisibility = {
  showBoard: true,
  showCalculators: true,
  showImageGeneration: true,
  showVoiceInput: true,
  showFileBrowser: true,
  showMCPTools: true,
  showEntitySuggestions: true,
};

// ============================================================
// Migration helper for existing localStorage preferences
// ============================================================

function migrateFromLocalStorage(): Partial<PersonalisationState> {
  const migrations: Partial<PersonalisationState> = {};
  
  try {
    // Migrer skipDashboard depuis localStorage
    const existingSkipDashboard = localStorage.getItem('therese-skip-dashboard');
    if (existingSkipDashboard !== null) {
      migrations.skipDashboard = existingSkipDashboard === 'true';
      // Nettoyer l'ancienne clé localStorage
      localStorage.removeItem('therese-skip-dashboard');
    }
  } catch (error) {
    // Ignorer les erreurs de localStorage en mode privé, etc.
    console.warn('Failed to migrate from localStorage:', error);
  }
  
  return migrations;
}

// ============================================================
// Store Interface
// ============================================================

interface PersonalisationState {
  // US-PERS-06: UX Mode
  uxMode: UXMode;
  setUXMode: (mode: UXMode) => void;


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

  // Comportement au lancement
  skipDashboard: boolean;
  setSkipDashboard: (skip: boolean) => void;
}

export const usePersonalisationStore = create<PersonalisationState>()(
  persist(
    (set) => {
      // Effectuer la migration des données localStorage au premier chargement
      const migrations = migrateFromLocalStorage();
      
      return {
        // ============================================================
        // US-PERS-06: UX Mode
        // ============================================================

        uxMode: DEFAULT_UX_MODE,
        setUXMode: (mode) => set({ uxMode: mode }),

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

        // ============================================================
        // Comportement au lancement
        // ============================================================

        skipDashboard: migrations.skipDashboard ?? false,
        setSkipDashboard: (skip) => set({ skipDashboard: skip }),
      };
    },
    {
      name: 'therese-personalisation',
      // B-493 : seules les données de l'utilisateur sont persistées (pas les
      // fonctions ni les réglages dérivés), avec une version de schéma et une
      // migration qui rend leur type aux dates relues du stockage.
      version: 1,
      partialize: (state) => ({
        uxMode: state.uxMode,
        skipDashboard: state.skipDashboard,
        promptTemplates: state.promptTemplates,
        llmBehavior: state.llmBehavior,
      }),
      migrate: (persisted) => {
        const { shortcuts: _oublie, ...brut } = (persisted ?? {}) as Partial<PersonalisationState> & { shortcuts?: unknown };
        // B-337 : la personnalisation des raccourcis est retirée ; une ancienne
        // table `shortcuts` enregistrée est simplement oubliée (`_oublie`).
        void _oublie;
        const promptTemplates = (brut.promptTemplates ?? []).map((t) => ({
          ...t,
          createdAt: t.createdAt instanceof Date ? t.createdAt : new Date(t.createdAt as unknown as string),
        }));
        // Les champs absents d'un ancien stockage sont complétés par l'état courant au merge.
        return { ...brut, promptTemplates } as unknown as Pick<PersonalisationState, 'uxMode' | 'skipDashboard' | 'promptTemplates' | 'llmBehavior'>;
      },
    }
  )
);

