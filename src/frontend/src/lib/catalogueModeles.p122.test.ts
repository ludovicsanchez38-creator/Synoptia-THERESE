/**
 * P-122 (Ludo, 25/09/2026) : Claude Opus 5.5, GPT-6 Sol et GPT-6 Luna dans le
 * catalogue de repli de l'interface (Réglages et mise en route hors-ligne),
 * avec les mêmes têtes que le catalogue du moteur (`modeles_catalogue.py`).
 */
import { describe, expect, it } from 'vitest';

import { FOURNISSEURS } from './catalogueModeles';

function modeles(fournisseur: string) {
  const trouve = FOURNISSEURS.find((f) => f.id === fournisseur);
  if (!trouve) throw new Error(`fournisseur absent : ${fournisseur}`);
  return trouve.models;
}

describe('catalogue de repli : Opus 5.5, GPT-6 Sol et Luna (P-122)', () => {
  it('Claude Opus 5.5 est en tête d’Anthropic, recommandé', () => {
    expect(modeles('anthropic')[0]).toEqual({ id: 'claude-opus-5-5', name: 'Claude Opus 5.5', badge: 'Recommandé' });
    expect(modeles('anthropic').map((m) => m.id)).toContain('claude-opus-5');
  });

  it('GPT-6 Sol est en tête d’OpenAI, Astra et Luna suivent', () => {
    expect(modeles('openai').slice(0, 3).map((m) => m.id)).toEqual(['gpt-6-sol', 'gpt-6-astra', 'gpt-6-luna']);
    expect(modeles('openai')[0]).toMatchObject({ name: 'GPT-6 Sol', badge: 'Recommandé' });
    expect(modeles('openai').find((m) => m.id === 'gpt-6-luna')?.name).toBe('GPT-6 Luna');
  });

  it('un seul modèle recommandé par fournisseur', () => {
    for (const fournisseur of ['anthropic', 'openai']) {
      expect(modeles(fournisseur).filter((m) => m.badge === 'Recommandé')).toHaveLength(1);
    }
  });
});
