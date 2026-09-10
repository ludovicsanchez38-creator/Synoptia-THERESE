/**
 * THÉRÈSE V3 - Commands Store (Zustand)
 *
 * Store unifié pour toutes les commandes : builtins, skills, user, MCP.
 */

import { create } from 'zustand';
import type {
  CommandDefinition,
  CreateUserCommandRequest,
  UpdateUserCommandRequest,
  GenerateTemplateRequest,
  GenerateTemplateResponse,
} from '../types/command';
import {
  fetchCommands,
  createUserCommand,
  updateUserCommand,
  deleteUserCommand,
  generateTemplate,
} from '../services/api/commands-v3';

interface CommandsState {
  /** Toutes les commandes chargées */
  commands: CommandDefinition[];
  /** Chargement en cours */
  isLoading: boolean;
  /** Erreur éventuelle */
  error: string | null;

  /** Charge toutes les commandes depuis le backend */
  fetchCommands: (filters?: {
    category?: string;
    show_on_home?: boolean;
    show_in_slash?: boolean;
    source?: string;
  }) => Promise<void>;

  /** Commandes filtrées par catégorie */
  getByCategory: (category: string) => CommandDefinition[];

  /** Commandes pour la page d'accueil */
  getHomeCommands: () => CommandDefinition[];

  /** Commandes pour le menu slash */
  getSlashCommands: () => CommandDefinition[];

  /** Commandes utilisateur (éditables) */
  getUserCommands: () => CommandDefinition[];

  /** Récupérer une commande par ID */
  getCommand: (id: string) => CommandDefinition | undefined;

  /** Créer une commande utilisateur */
  createCommand: (data: CreateUserCommandRequest) => Promise<CommandDefinition>;

  /** Mettre à jour une commande utilisateur */
  updateCommand: (id: string, data: UpdateUserCommandRequest) => Promise<CommandDefinition>;

  /** Supprimer une commande utilisateur */
  deleteCommand: (id: string) => Promise<void>;

  /** RFC : générer un template de commande */
  generateTemplate: (data: GenerateTemplateRequest) => Promise<GenerateTemplateResponse>;
}

/** D132 : une écriture en panne laisse une trace lisible, puis relance pour l'appelant. */
function messageDe(err: unknown, repli: string): string {
  return err instanceof Error && err.message ? err.message : repli;
}

export const useCommandsStore = create<CommandsState>((set, get) => ({
  commands: [],
  isLoading: false,
  error: null,

  fetchCommands: async (filters) => {
    set({ isLoading: true, error: null });
    try {
      const commands = await fetchCommands(filters);
      set({ commands, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Erreur de chargement des commandes',
        isLoading: false,
      });
    }
  },

  getByCategory: (category: string) => {
    return get().commands.filter((c) => c.category === category);
  },

  getHomeCommands: () => {
    return get().commands.filter((c) => c.show_on_home);
  },

  getSlashCommands: () => {
    return get().commands.filter((c) => c.show_in_slash);
  },

  getUserCommands: () => {
    return get().commands.filter((c) => c.source === 'user');
  },

  getCommand: (id: string) => {
    return get().commands.find((c) => c.id === id);
  },

  createCommand: async (data) => {
    set({ error: null });
    try {
      const created = await createUserCommand(data);
      // Recharger les commandes
      await get().fetchCommands();
      return created;
    } catch (err) {
      set({ error: messageDe(err, 'Impossible de créer la commande') });
      throw err;
    }
  },

  updateCommand: async (id, data) => {
    set({ error: null });
    try {
      const updated = await updateUserCommand(id, data);
      // Recharger les commandes
      await get().fetchCommands();
      return updated;
    } catch (err) {
      set({ error: messageDe(err, 'Impossible de modifier la commande') });
      throw err;
    }
  },

  deleteCommand: async (id) => {
    set({ error: null });
    try {
      await deleteUserCommand(id);
    } catch (err) {
      set({ error: messageDe(err, 'Impossible de supprimer la commande') });
      throw err;
    }
    // Retirer du store
    set((state) => ({
      commands: state.commands.filter((c) => c.id !== id),
    }));
  },

  generateTemplate: async (data) => {
    return generateTemplate(data);
  },
}));
