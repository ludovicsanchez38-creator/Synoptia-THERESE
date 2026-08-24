/**
 * Le panneau des traitements : la promesse affichée est la promesse tenable.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  listerTraitements: vi.fn(),
  annulerTraitement: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { TraitementsPanel } from './TraitementsPanel';

import type { Traitement } from '../../services/api/processingTasks';

function traitement(part: Partial<Traitement>): Traitement {
  return {
    id: 't-1', type: 'chat', label: 'Une génération', state: 'running',
    step: null, progress: null, project_id: null, conversation_id: null,
    error: null, created_at: null, started_at: null, finished_at: null,
    can_cancel: true,
    ...part,
  } as Traitement;
}

describe('TraitementsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useProcessingTasksStore.setState({
      traitements: [], erreur: null, arretsDemandes: new Set(),
      panneauOuvert: true,
    });
  });

  it('affiche Arrêter quand c’est possible, et l’état honnête après le clic', async () => {
    useProcessingTasksStore.setState({
      traitements: [traitement({ id: 't-1', label: 'Synchronisation de projet' })],
    });
    apiMocks.annulerTraitement.mockResolvedValue({
      state: 'cancel_requested', resultat: 'accepted', transmise: true,
    });
    apiMocks.listerTraitements.mockResolvedValue([
      traitement({
        id: 't-1', label: 'Synchronisation de projet',
        state: 'cancel_requested', can_cancel: false,
      }),
    ]);

    render(<TraitementsPanel />);
    fireEvent.click(
      screen.getByRole('button', { name: 'Arrêter Synchronisation de projet' }),
    );

    await waitFor(() => {
      expect(apiMocks.annulerTraitement).toHaveBeenCalledWith('t-1');
      expect(
        screen.getByText(/Arrêt demandé - fin de l'étape en cours/),
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByRole('button', { name: /Arrêter Synchronisation/ }),
    ).not.toBeInTheDocument();
  });

  it('montre l’échec avec sa cause, sans bouton Arrêter', () => {
    useProcessingTasksStore.setState({
      traitements: [traitement({
        state: 'failed', can_cancel: false, error: 'disque fatigué',
      })],
    });

    render(<TraitementsPanel />);

    expect(screen.getByText('En échec')).toBeInTheDocument();
    expect(screen.getByText('disque fatigué')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Arrêter/ })).not.toBeInTheDocument();
  });

  it('affiche la progression d’un traitement en cours', () => {
    useProcessingTasksStore.setState({
      traitements: [traitement({ progress: 0.5, step: 'découpage' })],
    });

    render(<TraitementsPanel />);

    expect(screen.getByText(/découpage/)).toBeInTheDocument();
    expect(screen.getByText(/50\s?%/)).toBeInTheDocument();
  });
});
