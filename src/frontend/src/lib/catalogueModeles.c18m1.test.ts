/**
 * Lot M1 (9 octobre 2026) : le repli hors ligne et la décoration de la liste
 * servie portent les mêmes noms. La tête de chaque repli ne bouge pas.
 */
import { describe, expect, it } from 'vitest';

import { FOURNISSEURS, decorer } from './catalogueModeles';

function modeles(fournisseur: string) {
  const trouve = FOURNISSEURS.find((f) => f.id === fournisseur);
  if (!trouve) throw new Error(`fournisseur absent : ${fournisseur}`);
  return trouve.models;
}

const NOMS = {
  'claude-fable-5-1': { name: 'Claude Fable 5.1', badge: 'Le plus capable' },
  'claude-sonnet-5-5': { name: 'Claude Sonnet 5.5', badge: 'Équilibré' },
  'claude-haiku-5-5': { name: 'Claude Haiku 5.5', badge: 'Rapide' },
  'grok-4.7': { name: 'Grok 4.7' },
  'gemini-3.8-flash': { name: 'Gemini 3.8 Flash' },
  'mistral-large-4': { name: 'Mistral Large 4', badge: 'Préversion' },
} as const;

describe('repli et décoration des modèles du 9 octobre', () => {
  it('garde la tête de chaque liste de repli', () => {
    expect(modeles('anthropic')[0].id).toBe('claude-opus-5-5');
    expect(modeles('gemini')[0].id).toBe('gemini-3.1-pro-preview');
    expect(modeles('mistral')[0].id).toBe('mistral-large-latest');
    expect(modeles('grok')[0].id).toBe('grok-4.5');
    expect(modeles('openai')[0].id).toBe('gpt-6-sol');
  });

  it('ajoute les nouveaux identifiants une seule fois, avec le même nom partout', () => {
    for (const [id, nom] of Object.entries(NOMS)) {
      expect(decorer([id])[0]).toEqual({ id, ...nom });
      const dansLeRepli = FOURNISSEURS.flatMap((f) => f.models).filter((m) => m.id === id);
      expect(dansLeRepli).toEqual([{ id, ...nom }]);
    }
  });

  it('laisse un seul recommandé chez Claude', () => {
    expect(modeles('anthropic').filter((m) => m.badge === 'Recommandé')).toHaveLength(1);
  });
});
