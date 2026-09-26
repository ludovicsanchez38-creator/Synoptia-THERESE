/**
 * P-148, lot 4 : la phrase qui dit ce que la suppression d'un projet emporte.
 * Familles non nulles écrites, familles à zéro omises, et jamais un « 0 tâche »
 * inventé quand une famille n'a pas pu être lue.
 */
import { describe, expect, it } from 'vitest';
import type { EnsembleDuProjet } from '../services/api';
import { consequencesDeLaSuppression } from './consequencesDeLaSuppression';

function totaux(t: {
  taches?: number; livrables?: number; deposes?: number; surPlace?: number; rattache?: boolean; planning?: number;
  conversations?: number; documents?: number; rendez_vous?: number; ranges?: number; associeHorsProjet?: boolean;
  sous_dossiers?: number;
}): EnsembleDuProjet {
  const ranges = t.ranges ?? 0;
  return {
    conversations: { total: t.conversations ?? 0, elements: [] },
    documents: { total: t.documents ?? 0, elements: [] },
    taches: { total: t.taches ?? 0, ouvertes: 0, en_retard: 0, elements: [] },
    // `total` compte les personnes distinctes, associé compris ; `ranges`
    // seulement les contacts rangés dans le projet.
    contacts: { total: ranges + (t.associeHorsProjet ? 1 : 0), ranges, elements: [] },
    livrables: { total: t.livrables ?? 0 },
    fichiers: {
      total: (t.deposes ?? 0) + (t.surPlace ?? 0),
      deposes: t.deposes ?? 0,
      indexes_sur_place: t.surPlace ?? 0,
    },
    dossier_synchronise: { rattache: t.rattache ?? false },
    rendez_vous: { total: t.rendez_vous ?? 0 },
    sous_dossiers: { total: t.sous_dossiers ?? 0 },
    planning: { total: t.planning ?? 0 },
    indisponibles: [],
  };
}

describe('P-148 : ce que la suppression d’un projet emporte', () => {
  it('écrit chaque famille non nulle, dans l’ordre de la RFC', () => {
    expect(consequencesDeLaSuppression(totaux({
      taches: 9, livrables: 3, deposes: 12, planning: 1,
      conversations: 7, documents: 2, rendez_vous: 2, ranges: 2, sous_dossiers: 1,
    }))).toEqual([
      'La suppression emporte 9 tâches, 3 livrables, 12 fichiers déposés dans THÉRÈSE et son planning calculé.',
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

  it('revue P-148, constat 3 : les fichiers du dossier synchronisé restent sur le disque, et le dossier est détaché', () => {
    expect(consequencesDeLaSuppression(totaux({ deposes: 1, surPlace: 4, rattache: true }))).toEqual([
      'La suppression emporte 1 fichier déposé dans THÉRÈSE.',
      '4 fichiers indexés depuis ton disque sortent de l’index ; ils restent sur ton disque.',
      'Le dossier synchronisé est détaché du projet ; il reste sur ton disque.',
    ]);
    expect(consequencesDeLaSuppression(totaux({ surPlace: 1 }))).toEqual([
      '1 fichier indexé depuis ton disque sort de l’index ; il reste sur ton disque.',
    ]);
  });

  it('revue P-148, constat 4 : seuls les contacts rangés passent en Global, pas le contact associé', () => {
    expect(consequencesDeLaSuppression(totaux({ ranges: 2, associeHorsProjet: true }))).toEqual([
      '2 contacts rangés dans ce projet passent en Global, visibles dans toutes les conversations.',
    ]);
    // Un seul contact, l'associé, hors du projet : rien ne passe en Global.
    expect(consequencesDeLaSuppression(totaux({ associeHorsProjet: true }))).toEqual([]);
  });

  it('un projet vide n’annonce rien de plus', () => {
    expect(consequencesDeLaSuppression(totaux({}))).toEqual([]);
  });

  it('une famille illisible fait renoncer à la phrase, jamais « 0 tâche »', () => {
    expect(consequencesDeLaSuppression({ ...totaux({ livrables: 3 }), taches: null, indisponibles: ['taches'] })).toBeNull();
    expect(consequencesDeLaSuppression({ ...totaux({ taches: 2 }), planning: null, indisponibles: ['planning'] })).toBeNull();
    expect(consequencesDeLaSuppression({ ...totaux({ taches: 2 }), dossier_synchronise: null, indisponibles: ['dossier_synchronise'] })).toBeNull();
  });
});
