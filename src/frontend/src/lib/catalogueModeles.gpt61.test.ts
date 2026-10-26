/**
 * Lot M2 : GPT-6.1 Sol dans le repli, sans prendre la tête ni un badge de
 * préversion (la fiche OpenAI ne le dit pas).
 */
import { describe, expect, it } from 'vitest';

import { FOURNISSEURS } from './catalogueModeles';

describe('repli OpenAI : gpt-6.1-sol (lot M2)', () => {
  const openai = FOURNISSEURS.find((f) => f.id === 'openai');

  it('reste après Sol, Astra et Luna, sans badge', () => {
    if (!openai) throw new Error('openai absent');
    const ids = openai.models.map((m) => m.id);
    expect(ids.slice(0, 3)).toEqual(['gpt-6-sol', 'gpt-6-astra', 'gpt-6-luna']);
    expect(ids.indexOf('gpt-6.1-sol')).toBeGreaterThan(ids.indexOf('gpt-6-luna'));
    const fiche = openai.models.find((m) => m.id === 'gpt-6.1-sol');
    expect(fiche).toMatchObject({ id: 'gpt-6.1-sol', name: 'GPT-6.1 Sol' });
    expect(fiche?.badge).toBeUndefined();
  });
});

describe('repli OpenAI : gpt-6.1-terra (26/10/2026)', () => {
  const openai = FOURNISSEURS.find((f) => f.id === 'openai');

  it('suit 6.1 Sol, sans badge, et garde l’ancien Terra', () => {
    if (!openai) throw new Error('openai absent');
    const ids = openai.models.map((m) => m.id);
    expect(ids.slice(0, 3)).toEqual(['gpt-6-sol', 'gpt-6-astra', 'gpt-6-luna']);
    expect(ids.indexOf('gpt-6.1-terra')).toBe(ids.indexOf('gpt-6.1-sol') + 1);
    expect(ids).toContain('gpt-5.6-terra');
    const fiche = openai.models.find((m) => m.id === 'gpt-6.1-terra');
    expect(fiche).toMatchObject({ id: 'gpt-6.1-terra', name: 'GPT-6.1 Terra' });
    expect(fiche?.badge).toBeUndefined();
  });
});
