/** B-595 : un nom accentué donnait un slug amputé (« Résumé » -> « r-sum »), un nom non latin un slug vide. */
import { describe, expect, it } from 'vitest';

import { slugDeCommande } from './slugDeCommande';

describe('slugDeCommande', () => {
  it('ramène les lettres accentuées à leur base', () => {
    expect(slugDeCommande('Résumé de réunion')).toBe('resume-de-reunion');
    expect(slugDeCommande('Éléments à vérifier')).toBe('elements-a-verifier');
  });

  it('ne rend jamais une chaîne vide', () => {
    expect(slugDeCommande('日本語')).toBe('commande');
    expect(slugDeCommande('   ')).toBe('commande');
  });

  it('garde les noms simples inchangés', () => {
    expect(slugDeCommande('Relance clients')).toBe('relance-clients');
  });
});
