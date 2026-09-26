/**
 * P-148, lot 4 : la phrase qui dit ce que la suppression d'un projet emporte.
 * Familles non nulles écrites, familles à zéro omises, et jamais un « 0 tâche »
 * inventé quand une famille n'a pas pu être lue.
 */
import { describe, expect, it } from 'vitest';
import type { EnsembleDuProjet } from '../services/api';
import { consequencesDeLaSuppression } from './consequencesDeLaSuppression';

function totaux(t: {
  taches?: number; livrables?: number; fichiers?: number; planning?: number;
  conversations?: number; documents?: number; rendez_vous?: number; ranges?: number; sous_dossiers?: number;
}): EnsembleDuProjet {
  return {
    conversations: { total: t.conversations ?? 0, elements: [] },
    documents: { total: t.documents ?? 0, elements: [] },
    taches: { total: t.taches ?? 0, ouvertes: 0, en_retard: 0, elements: [] },
    contacts: { total: t.ranges ?? 0, ranges: t.ranges ?? 0, elements: [] },
    livrables: { total: t.livrables ?? 0 },
    fichiers: { total: t.fichiers ?? 0 },
    rendez_vous: { total: t.rendez_vous ?? 0 },
    sous_dossiers: { total: t.sous_dossiers ?? 0 },
    planning: { total: t.planning ?? 0 },
    indisponibles: [],
  };
}

describe('P-148 : ce que la suppression d’un projet emporte', () => {
  it('écrit chaque famille non nulle, dans l’ordre de la RFC', () => {
    expect(consequencesDeLaSuppression(totaux({
      taches: 9, livrables: 3, fichiers: 12, planning: 1,
      conversations: 7, documents: 2, rendez_vous: 2, ranges: 2, sous_dossiers: 1,
    }))).toEqual([
      'La suppression emporte 9 tâches, 3 livrables, 12 fichiers joints et son planning calculé.',
      '7 conversations, 2 documents et 2 rendez-vous restent, sans lien avec le projet.',
      'Ces conversations ne liront plus que les documents généraux.',
      '2 contacts et 1 sous-projet rangés dans ce projet passent en Global, visibles dans toutes les conversations.',
    ]);
  });

  it('omet les familles à zéro et accorde au singulier', () => {
    expect(consequencesDeLaSuppression(totaux({ taches: 1, conversations: 1, ranges: 1 }))).toEqual([
      'La suppression emporte 1 tâche.',
      '1 conversation reste, sans lien avec le projet.',
      'Cette conversation ne lira plus que les documents généraux.',
      '1 contact rangé dans ce projet passe en Global, visible dans toutes les conversations.',
    ]);
  });

  it('un projet vide n’annonce rien de plus', () => {
    expect(consequencesDeLaSuppression(totaux({}))).toEqual([]);
  });

  it('une famille illisible fait renoncer à la phrase, jamais « 0 tâche »', () => {
    expect(consequencesDeLaSuppression({ ...totaux({ livrables: 3 }), taches: null, indisponibles: ['taches'] })).toBeNull();
    expect(consequencesDeLaSuppression({ ...totaux({ taches: 2 }), planning: null, indisponibles: ['planning'] })).toBeNull();
  });
});
