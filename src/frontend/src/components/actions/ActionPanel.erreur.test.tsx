/**
 * B-374 (05/09/2026) : le panneau d'actions ignorait le champ `error` du
 * store. Un échec de chargement s'affichait « Aucune action disponible. »,
 * sans cause ni reprise.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useActionsStore } from '../../stores/actionsStore';
import { ActionPanel } from './ActionPanel';

describe("B-374 - un échec de chargement ne se déguise pas en liste vide", () => {
  it('affiche la cause, propose Réessayer, et cache « Aucune action »', () => {
    const loadAgents = vi.fn(async () => {});
    useActionsStore.setState({
      agents: [],
      isLoading: false,
      isPanelOpen: true,
      error: 'Impossible de contacter le serveur',
      loadAgents,
    } as never);

    render(<ActionPanel />);

    const alerte = screen.getByRole('alert');
    expect(alerte.textContent).toMatch(/Impossible de contacter le serveur/);
    expect(screen.queryByText(/Aucune action disponible/)).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /Réessayer/ }));
    expect(loadAgents).toHaveBeenCalled();
  });
});
