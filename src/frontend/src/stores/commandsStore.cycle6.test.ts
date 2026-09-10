/**
 * Cycle 6, lecteur D132 (stores/commandsStore.ts) : create, update et delete
 * n'écrivaient jamais `error`. Sur l'Accueil, supprimer une commande perso en
 * panne ne laissait aucune trace lisible, et une erreur de lecture précédente
 * restait affichée après une écriture réussie.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  fetchCommands: vi.fn(),
  createUserCommand: vi.fn(),
  updateUserCommand: vi.fn(),
  deleteUserCommand: vi.fn(),
  generateTemplate: vi.fn(),
}));
vi.mock('../services/api/commands-v3', () => api);

import { useCommandsStore } from './commandsStore';

const perso = { id: 'user-relance', name: 'relance', source: 'user', category: 'organiser', show_on_home: true, show_in_slash: true } as never;

beforeEach(() => {
  vi.clearAllMocks();
  api.fetchCommands.mockResolvedValue([perso]);
  useCommandsStore.setState({ commands: [perso], error: null, isLoading: false });
});

describe('D132 : les écritures du store de commandes disent leurs pannes', () => {
  it('une suppression en panne pose error, garde la commande et relance', async () => {
    api.deleteUserCommand.mockRejectedValue(new Error('Le serveur ne répond pas'));
    await expect(useCommandsStore.getState().deleteCommand('user-relance')).rejects.toThrow('Le serveur ne répond pas');
    expect(useCommandsStore.getState().error).toBe('Le serveur ne répond pas');
    expect(useCommandsStore.getState().commands).toHaveLength(1);
  });

  it('une création en panne pose error', async () => {
    api.createUserCommand.mockRejectedValue(new Error('Nom déjà pris'));
    await expect(useCommandsStore.getState().createCommand({ name: 'x' } as never)).rejects.toThrow();
    expect(useCommandsStore.getState().error).toBe('Nom déjà pris');
  });

  it('une mise à jour en panne pose error', async () => {
    api.updateUserCommand.mockRejectedValue(new Error('Catégorie inconnue'));
    await expect(useCommandsStore.getState().updateCommand('user-relance', { category: 'zzz' } as never)).rejects.toThrow();
    expect(useCommandsStore.getState().error).toBe('Catégorie inconnue');
  });

  it('une écriture réussie efface une erreur précédente', async () => {
    useCommandsStore.setState({ error: 'Ancienne panne' });
    api.deleteUserCommand.mockResolvedValue(undefined);
    await useCommandsStore.getState().deleteCommand('user-relance');
    expect(useCommandsStore.getState().error).toBeNull();
    expect(useCommandsStore.getState().commands).toHaveLength(0);
  });
});
