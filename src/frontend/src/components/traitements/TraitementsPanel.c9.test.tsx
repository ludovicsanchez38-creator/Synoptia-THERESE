/**
 * B-764 (cycle 9) : « Arrêt demandé » restait affiché sur un traitement déjà
 * terminé, en échec ou interrompu après une demande d'arrêt, parce que la
 * condition ne testait que l'état « cancelled ». Un état terminal se dit tel quel.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({ listerTraitements: vi.fn(), annulerTraitement: vi.fn() }));
vi.mock('../../services/api', () => apiMocks);

import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { TraitementsPanel } from './TraitementsPanel';
import type { Traitement } from '../../services/api/processingTasks';

function traitement(part: Partial<Traitement>): Traitement {
  return {
    id: 't-1', type: 'chat', label: 'Synchronisation de projet', state: 'running',
    step: null, progress: null, project_id: null, conversation_id: null,
    error: null, created_at: null, started_at: null, finished_at: null,
    can_cancel: false,
    ...part,
  } as Traitement;
}

describe('TraitementsPanel - B-764, un état terminal se dit tel quel après une demande d’arrêt', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.listerTraitements.mockImplementation(async () => useProcessingTasksStore.getState().traitements);
  });

  it.each([
    ['done', 'Terminé'],
    ['failed', 'En échec'],
    ['interrupted', 'Interrompu (redémarrage)'],
  ] as const)('%s après une demande d’arrêt affiche « %s », pas « Arrêt demandé »', (state, libelle) => {
    useProcessingTasksStore.setState({
      traitements: [traitement({ id: 't-1', state })],
      erreur: null, arretsDemandes: new Set(['t-1']), panneauOuvert: true,
    });
    render(<TraitementsPanel />);
    expect(screen.getByText((_, el) => el?.tagName === 'P' && (el.textContent ?? '').includes(libelle))).toBeInTheDocument();
    expect(screen.queryByText(/Arrêt demandé/)).toBeNull();
  });

  it('garde « Arrêt demandé » tant que le traitement tourne encore', () => {
    useProcessingTasksStore.setState({
      traitements: [traitement({ id: 't-1', state: 'running' })],
      erreur: null, arretsDemandes: new Set(['t-1']), panneauOuvert: true,
    });
    render(<TraitementsPanel />);
    expect(screen.getByText(/Arrêt demandé/)).toBeInTheDocument();
  });
});
