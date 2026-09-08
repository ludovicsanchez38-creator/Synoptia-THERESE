/** P-051 (Nadia, étape 31) : un agent d'action ne part plus au premier clic ; toute entrée ouvre sa fiche, où « Lancer » confirme. */
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../services/api/actions', () => ({
  fetchActions: vi.fn(), fetchAction: vi.fn(), runAction: vi.fn(), fetchTask: vi.fn(), fetchTasks: vi.fn(), cancelTask: vi.fn(),
}));

import { runAction } from '../services/api/actions';
import { useActionsStore } from './actionsStore';
import type { ActionAgent } from '../services/api/actions';

const relance: ActionAgent = {
  id: 'relance-clients', name: 'Relance clients', description: 'Relance les factures échues', icon: 'Mail', category: 'commercial', steps_count: 3, params: [],
} as unknown as ActionAgent;

describe('actionsStore.ouvrirLaFicheAgent (P-051)', () => {
  beforeEach(() => {
    useActionsStore.setState({ agents: [relance], selectedAgent: null, isPanelOpen: false, error: null });
  });

  it('ouvre le panneau et sélectionne l’agent sans rien lancer, même sans paramètre', () => {
    useActionsStore.getState().ouvrirLaFicheAgent(relance);
    const etat = useActionsStore.getState();
    expect(etat.isPanelOpen).toBe(true);
    expect(etat.selectedAgent?.id).toBe('relance-clients');
    expect(runAction).not.toHaveBeenCalled();
  });
});
