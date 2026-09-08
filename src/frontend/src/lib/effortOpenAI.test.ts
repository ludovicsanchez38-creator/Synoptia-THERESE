/** P-045 : le prédicat frontend suit le backend (_uses_max_completion_tokens) sur des témoins partagés. */
import { describe, expect, it } from 'vitest';

import temoins from './effortOpenAI.temoins.json';
import { effortTransmisSansOutils, modeleOpenAIRaisonnant } from './effortOpenAI';

describe('effortOpenAI (P-045)', () => {
  it.each(Object.entries(temoins.temoins))('%s → famille raisonnante : %s', (modele, attendu) => {
    expect(modeleOpenAIRaisonnant(modele)).toBe(attendu);
  });

  it('seuls les GPT-5.6 reçoivent l’effort sans outils, comme le catalogue backend', () => {
    for (const modele of temoins.effort_transmis_sans_outils) expect(effortTransmisSansOutils(modele)).toBe(true);
    expect(effortTransmisSansOutils('gpt-5.5')).toBe(false);
    expect(effortTransmisSansOutils('gpt-5.4-mini')).toBe(false);
  });
});
