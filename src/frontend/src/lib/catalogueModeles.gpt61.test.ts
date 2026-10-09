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
