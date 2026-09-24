/**
 * B-1160 (cycle 13, lecteur B) : le libellé et l'erreur d'un travail étaient
 * tronqués (classe truncate) sans aucun moyen de lire la suite. L'erreur,
 * qui dit quoi faire, s'affiche désormais en entier ; le libellé garde sa
 * ligne unique et son texte complet en infobulle.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  listerTraitements: vi.fn(),
  annulerTraitement: vi.fn(),
}));
vi.mock('../../services/api', () => apiMocks);

import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { TraitementsPanel } from './TraitementsPanel';
import type { Traitement } from '../../services/api/processingTasks';

const LIBELLE = 'Synchronisation du projet Rénovation de la grange familiale, trois niveaux, avec les plans';
const ERREUR = "Le service d'IA est indisponible pour l'instant (erreur 529). Réessaie dans un moment ou choisis un autre modèle.";

describe('B-1160 troncature des travaux', () => {
  beforeEach(() => {
    apiMocks.listerTraitements.mockResolvedValue([]);
    useProcessingTasksStore.setState({
      traitements: [{
        id: 't-1', type: 'chat', label: LIBELLE, state: 'failed',
        step: null, progress: null, project_id: null, conversation_id: null,
        error: ERREUR, created_at: null, started_at: null, finished_at: null,
        can_cancel: false,
      } as Traitement],
      erreur: null, arretsDemandes: new Set(), panneauOuvert: true,
    });
  });

  it('un texte tronqué garde un moyen d’être lu en entier', () => {
    render(<TraitementsPanel />);
    const lisibles = [LIBELLE, ERREUR].map((texte) => {
      const el = screen.getByText(texte);
      const tronque = el.classList.contains('truncate');
      const recours = el.getAttribute('title') === texte
        || el.closest('[title]')?.getAttribute('title') === texte;
      return { texte: texte.slice(0, 20), tronque, recours };
    });
    expect(lisibles.filter((l) => l.tronque && !l.recours)).toEqual([]);
    expect(screen.getByText(ERREUR).classList.contains('truncate')).toBe(false);
  });
});
