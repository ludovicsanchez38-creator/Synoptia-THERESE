import { describe, expect, it } from 'vitest';

import { classerCommandes } from './classerCommandes';

const commandes = [
  { name: 'Tâches', description: 'Ouvrir les tâches ; les conversations y renvoient', keywords: ['todo'] },
  { name: 'Conversations', description: 'Ouvrir le tiroir', keywords: ['historique'] },
  { name: 'Agenda', description: 'Rendez-vous', keywords: ['conversations'] },
];

describe('classerCommandes (B-613)', () => {
  it('le nom exact passe avant le mot-clé, qui passe avant la description', () => {
    expect(classerCommandes(commandes, 'Conversations').map((c) => c.name)).toEqual(['Conversations', 'Agenda', 'Tâches']);
  });

  it('ignore les accents et la casse', () => {
    expect(classerCommandes(commandes, 'taches').map((c) => c.name)).toEqual(['Tâches']);
  });

  it('sans recherche, garde l’ordre d’origine', () => {
    expect(classerCommandes(commandes, '  ').map((c) => c.name)).toEqual(['Tâches', 'Conversations', 'Agenda']);
  });
});
