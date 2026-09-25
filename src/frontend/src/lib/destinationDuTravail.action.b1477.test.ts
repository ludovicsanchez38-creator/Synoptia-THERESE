/**
 * B-1477 (recette P-146, lot 5, KO-5) : une action guidée terminée n'était
 * plus consultable une fois son panneau fermé ; sa ligne dans « Travaux »
 * restait un texte inerte, alors que le travail porte l'identifiant de la
 * tâche (entity_id) et que le moteur la relit (GET /api/actions/tasks/{id}).
 */
import { describe, expect, it, vi } from 'vitest';
import type { Traitement } from '../services/api';
import { destinationDuTravail, ouvrirLeTravail } from './destinationDuTravail';

function travail(partiel: Partial<Traitement>): Traitement {
  return {
    id: 'tr-1', type: 'action', label: 'Audit trésorerie', state: 'done', step: null, progress: null, project_id: null,
    conversation_id: null, entity_id: null, error: null, created_at: null, started_at: null, finished_at: null,
    can_cancel: false, ...partiel,
  };
}

describe('B-1477 : une action guidée mène à son résultat', () => {
  it('terminée ou en cours, elle a une destination', () => {
    expect(destinationDuTravail(travail({ entity_id: 'tache-1' }))).toEqual({ kind: 'action', id: 'tache-1' });
    expect(destinationDuTravail(travail({ entity_id: 'tache-2', state: 'running' }))).toEqual({ kind: 'action', id: 'tache-2' });
  });
  it('sans identifiant de tâche, pas de destination inventée', () => {
    expect(destinationDuTravail(travail({ entity_id: null }))).toBeNull();
  });
  it('ouvrir la destination ouvre la tâche', () => {
    const a = { ouvrirVue: vi.fn(), ouvrirDocument: vi.fn(), ouvrirConversation: vi.fn(), ouvrirScenario: vi.fn(), ouvrirAction: vi.fn() };
    ouvrirLeTravail({ kind: 'action', id: 'tache-1' }, a);
    expect(a.ouvrirAction).toHaveBeenCalledWith('tache-1');
  });
});
