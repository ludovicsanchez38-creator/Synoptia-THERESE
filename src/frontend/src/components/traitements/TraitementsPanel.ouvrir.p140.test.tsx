/**
 * P-140 : une ligne de « Travaux » qui connaît son objet l'ouvre, et le
 * panneau se ferme ; une ligne sans objet connu reste un texte.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { EVENEMENT_OUVRIR_TRAVAIL } from '../../lib/destinationDuTravail';
import { TraitementsPanel } from './TraitementsPanel';

const base = {
  step: null, progress: null, project_id: null, conversation_id: null, error: null,
  created_at: null, started_at: null, finished_at: null, can_cancel: false,
};

describe('P-140 : ouvrir l’objet d’un travail', () => {
  const fermer = vi.fn();
  beforeEach(() => {
    fermer.mockReset();
    useProcessingTasksStore.setState({
      traitements: [
        { ...base, id: 't1', type: 'document_outline', label: 'Trame : Plan de formation', state: 'running', entity_id: 'doc-1' },
        { ...base, id: 't2', type: 'inconnu', label: 'Travail sans objet', state: 'done', entity_id: null },
      ],
      erreur: null, arretsDemandes: new Set(), fermerPanneau: fermer,
    } as never);
  });

  it('la trame en cours ouvre son document et ferme le panneau', () => {
    const ecoute = vi.fn();
    window.addEventListener(EVENEMENT_OUVRIR_TRAVAIL, ecoute);
    render(<TraitementsPanel />);
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir Trame : Plan de formation' }));
    window.removeEventListener(EVENEMENT_OUVRIR_TRAVAIL, ecoute);
    expect(ecoute).toHaveBeenCalledTimes(1);
    expect((ecoute.mock.calls[0][0] as CustomEvent).detail).toEqual({ kind: 'document', id: 'doc-1' });
    expect(fermer).toHaveBeenCalled();
  });

  it('un travail sans objet connu reste un texte', () => {
    render(<TraitementsPanel />);
    expect(screen.getByText('Travail sans objet')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Ouvrir Travail sans objet' })).toBeNull();
  });
});
