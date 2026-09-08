/**
 * B-637 (persona Nadia, c4) : la palette de la coque filtre deux listes
 * (capacités, puis commandes de l'application) sans aucun classement ; la
 * première liste passe toujours devant. Taper « Conversations » sélectionnait
 * « Tâches » (une capacité dont la description contient le mot) alors que la
 * commande « Conversations » existait dans la seconde liste. Le correctif
 * B-613 (classerCommandes) avait été posé sur l'autre palette.
 */
import { describe, expect, it } from 'vitest';
import { classerCommandes, indexDeLaMeilleureOption } from './classerCommandes';

const capacites = [
  { name: 'Tâches', description: 'Créer, prioriser et terminer les actions issues des conversations', keywords: ['todo'] },
  { name: 'Agenda', description: 'Préparer les rendez-vous', keywords: [] },
];
const commandes = [
  { name: 'Conversations', description: 'Ouvrir la liste des conversations', keywords: ['historique'] },
  { name: 'Effacer la conversation', description: 'Supprimer tous les messages', keywords: ['vider'] },
];

describe('B-637 : la meilleure correspondance de la palette, toutes listes confondues', () => {
  it('« Conversations » désigne la commande du même nom, pas la capacité qui en parle', () => {
    const groupes = [classerCommandes(capacites, 'Conversations'), classerCommandes(commandes, 'Conversations')];
    // Index plat : les capacités retenues d'abord, puis les commandes.
    expect(indexDeLaMeilleureOption(groupes, 'Conversations')).toBe(groupes[0].length);
    expect(groupes[1][0].name).toBe('Conversations');
  });

  it('sans recherche ou sans correspondance, la première option reste sélectionnée', () => {
    expect(indexDeLaMeilleureOption([capacites, commandes], '')).toBe(0);
    expect(indexDeLaMeilleureOption([[], []], 'xyz')).toBe(0);
  });

  it('à rang égal, la liste placée devant garde la main', () => {
    const groupes = [classerCommandes(capacites, 'Agenda'), classerCommandes(commandes, 'Agenda')];
    expect(indexDeLaMeilleureOption(groupes, 'Agenda')).toBe(0);
  });
});
