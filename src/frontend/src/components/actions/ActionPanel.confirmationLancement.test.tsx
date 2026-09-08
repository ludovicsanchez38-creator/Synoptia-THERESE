/** P-051 (Nadia, étape 31) : « Relance clients » démarrait au premier clic sur sa carte, sans fiche ni confirmation. Tout agent passe par sa fiche ; « Lancer » confirme ; une erreur de lancement s'affiche dans la fiche. */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/actions', () => ({
  fetchActions: vi.fn(async () => []), fetchAction: vi.fn(), runAction: vi.fn(), fetchTask: vi.fn(), fetchTasks: vi.fn(async () => []), cancelTask: vi.fn(),
}));

import { runAction } from '../../services/api/actions';
import { useActionsStore } from '../../stores/actionsStore';
import type { ActionAgent } from '../../services/api/actions';
import { ActionPanel } from './ActionPanel';

const relance: ActionAgent = {
  id: 'relance-clients', name: 'Relance clients', description: 'Relance les factures échues par e-mail', icon: 'Mail', category: 'commercial', steps_count: 3, params: [],
} as unknown as ActionAgent;

describe('ActionPanel : confirmer le lancement (P-051)', () => {
  beforeEach(() => {
    vi.mocked(runAction).mockReset();
    useActionsStore.setState({ agents: [relance], selectedAgent: null, isPanelOpen: true, isLoading: false, error: null, tasks: [], activeTask: null, loadAgents: vi.fn(async () => {}) } as never);
  });

  it('un agent sans paramètre ouvre sa fiche au clic, ne se lance pas, et la fiche prend le focus', async () => {
    render(<ActionPanel />);
    fireEvent.click(screen.getByRole('button', { name: /Relance clients/ }));
    expect(runAction).not.toHaveBeenCalled();
    const titre = await screen.findByRole('heading', { name: 'Relance clients' });
    await waitFor(() => expect(document.activeElement).toBe(titre));
    expect(screen.getByText('Relance les factures échues par e-mail')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retour au catalogue' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Lancer/ }));
    expect(runAction).toHaveBeenCalledWith('relance-clients', {});
  });

  it('une erreur de lancement s’affiche dans la fiche, qui reste ouverte avec « Lancer »', async () => {
    vi.mocked(runAction).mockRejectedValue(new Error('Service indisponible'));
    render(<ActionPanel />);
    fireEvent.click(screen.getByRole('button', { name: /Relance clients/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Lancer/ }));
    const alerte = await screen.findByRole('alert');
    expect(alerte).toHaveTextContent('Service indisponible');
    expect(screen.getByRole('heading', { name: 'Relance clients' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Lancer/ })).toBeInTheDocument();
  });

  it('« Retour au catalogue » rend le focus à la carte de l’agent', async () => {
    render(<ActionPanel />);
    fireEvent.click(screen.getByRole('button', { name: /Relance clients/ }));
    fireEvent.click(await screen.findByRole('button', { name: 'Retour au catalogue' }));
    const carte = await screen.findByRole('button', { name: /Relance clients/ });
    await waitFor(() => expect(document.activeElement).toBe(carte));
  });
});
