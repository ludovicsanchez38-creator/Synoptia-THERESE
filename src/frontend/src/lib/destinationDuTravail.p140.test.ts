/**
 * P-140 (persona Zoé, cycle 13) : dans « Travaux », les lignes étaient des
 * textes inertes, alors que c'était le seul endroit qui savait que la trame
 * tournait. Chaque ligne ouvre l'objet qu'elle nomme quand on le connaît.
 */
import { describe, expect, it, vi } from 'vitest';
import type { Traitement } from '../services/api';
import { destinationDuTravail, ouvrirLeTravail } from './destinationDuTravail';

function travail(partiel: Partial<Traitement>): Traitement {
  return {
    id: 'tr-1', type: 'chat', label: 'Travail', state: 'done', step: null, progress: null, project_id: null,
    conversation_id: null, entity_id: null, error: null, created_at: null, started_at: null, finished_at: null,
    can_cancel: false, ...partiel,
  };
}

describe('P-140 : la destination d’un travail', () => {
  it('une trame mène à son document', () => {
    expect(destinationDuTravail(travail({ type: 'document_outline', entity_id: 'doc-1' }))).toEqual({ kind: 'document', id: 'doc-1' });
  });
  it('une réponse ou une recherche approfondie mène à sa conversation', () => {
    expect(destinationDuTravail(travail({ type: 'chat', conversation_id: 'conv-1' }))).toEqual({ kind: 'conversation', id: 'conv-1' });
    expect(destinationDuTravail(travail({ type: 'deep-research', conversation_id: 'conv-2' }))).toEqual({ kind: 'conversation', id: 'conv-2' });
  });
  it('une synchronisation de projet mène aux projets, une indexation aux fichiers', () => {
    expect(destinationDuTravail(travail({ type: 'project_sync', project_id: 'p-1' }))).toEqual({ kind: 'vue', vue: 'projects' });
    expect(destinationDuTravail(travail({ type: 'indexation' }))).toEqual({ kind: 'vue', vue: 'files' });
  });
  it('Décision et Atelier ne s’ouvrent que tant qu’ils tournent', () => {
    expect(destinationDuTravail(travail({ type: 'board', state: 'running' }))).toEqual({ kind: 'scenario', scenario: 'board' });
    expect(destinationDuTravail(travail({ type: 'atelier', state: 'queued' }))).toEqual({ kind: 'scenario', scenario: 'atelier' });
    expect(destinationDuTravail(travail({ type: 'board', state: 'done' }))).toBeNull();
  });
  it('sans objet connu, pas de destination inventée', () => {
    expect(destinationDuTravail(travail({ type: 'document_outline', entity_id: null }))).toBeNull();
    expect(destinationDuTravail(travail({ type: 'chat', conversation_id: null }))).toBeNull();
    expect(destinationDuTravail(travail({ type: 'inconnu' }))).toBeNull();
  });
});

describe('P-140 : ouvrir un travail', () => {
  function actions() {
    return { ouvrirVue: vi.fn(), ouvrirDocument: vi.fn(), ouvrirConversation: vi.fn(), ouvrirScenario: vi.fn(), ouvrirAction: vi.fn() };
  }
  it('un document ouvre la vue Documents puis le document', () => {
    const a = actions();
    ouvrirLeTravail({ kind: 'document', id: 'doc-1' }, a);
    expect(a.ouvrirVue).toHaveBeenCalledWith('documents');
    expect(a.ouvrirDocument).toHaveBeenCalledWith('doc-1');
  });
  it('une conversation, une vue et un scénario suivent chacun leur chemin', () => {
    const a = actions();
    ouvrirLeTravail({ kind: 'conversation', id: 'conv-1' }, a);
    ouvrirLeTravail({ kind: 'vue', vue: 'projects' }, a);
    ouvrirLeTravail({ kind: 'scenario', scenario: 'board' }, a);
    expect(a.ouvrirConversation).toHaveBeenCalledWith('conv-1');
    expect(a.ouvrirVue).toHaveBeenCalledWith('projects');
    expect(a.ouvrirScenario).toHaveBeenCalledWith('board');
  });
});
