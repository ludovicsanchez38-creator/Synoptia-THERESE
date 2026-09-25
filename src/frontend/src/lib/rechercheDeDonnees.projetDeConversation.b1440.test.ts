/**
 * B-1440 (recette P-146, lot 2, H2) : dans la palette, « Garnier » trouvait le
 * contact et le projet « Agencement boutique Garnier », mais pas la
 * conversation rattachée à ce projet, que le tiroir trouve (P-127). La
 * conversation se cherche aussi par le nom de son projet, et le dit.
 */
import { describe, expect, it } from 'vitest';

import type { Project } from '../services/api/memory';
import type { Conversation } from '../stores/chatStore';
import { chercherDansLesDonnees } from './rechercheDeDonnees';

const PROJET = { id: 'p-garnier', name: 'Agencement boutique Garnier', description: null, tags: [] } as unknown as Project;
const CONVERSATION = {
  id: 'conv-1', title: 'Plan de la vitrine', messages: [], projectId: 'p-garnier',
} as unknown as Conversation;

describe('B-1440 : une conversation se retrouve par son projet', () => {
  it('« Garnier » ramène la conversation rattachée, nommée par son projet', () => {
    const resultats = chercherDansLesDonnees('garnier', { contacts: [], projets: [PROJET], conversations: [CONVERSATION] });
    expect(resultats.conversations).toEqual([
      { kind: 'conversation', id: 'conv-1', titre: 'Plan de la vitrine', detail: 'Conversation · Projet : Agencement boutique Garnier' },
    ]);
  });
});
