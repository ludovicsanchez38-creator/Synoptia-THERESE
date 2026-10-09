/** P-045 : le prédicat frontend suit le backend (_uses_max_completion_tokens) sur des témoins partagés. */
import { describe, expect, it } from 'vitest';

import temoins from './effortOpenAI.temoins.json';
import { effortConserveAvecOutils, effortTransmisSansOutils, modeleOpenAIRaisonnant } from './effortOpenAI';

describe('effortOpenAI (P-045)', () => {
  it.each(Object.entries(temoins.temoins))('%s → famille raisonnante : %s', (modele, attendu) => {
    // B-1774 : Astra exige Responses pour les outils (none y est un 400).
    // Le témoin reste vrai pour _uses_max_completion_tokens ; l'écran ne
    // doit plus dire que l'effort est coupé.
    if (modele.toLowerCase() === 'gpt-6-astra') {
      expect(effortConserveAvecOutils(modele)).toBe(true);
      expect(modeleOpenAIRaisonnant(modele)).toBe(false);
      return;
    }
    expect(modeleOpenAIRaisonnant(modele)).toBe(attendu);
  });

  it('seuls les GPT-5.6 reçoivent l’effort sans outils, comme le catalogue backend', () => {
    for (const modele of temoins.effort_transmis_sans_outils) expect(effortTransmisSansOutils(modele)).toBe(true);
    expect(effortTransmisSansOutils('gpt-5.5')).toBe(false);
    expect(effortTransmisSansOutils('gpt-5.4-mini')).toBe(false);
  });

  it('gpt-6.1-sol garde l’effort avec les outils et le transmet sans outils', () => {
    expect(modeleOpenAIRaisonnant('gpt-6.1-sol')).toBe(false);
    expect(effortConserveAvecOutils('gpt-6.1-sol')).toBe(true);
    expect(effortTransmisSansOutils('gpt-6.1-sol')).toBe(true);
    expect(effortConserveAvecOutils('gpt-6-sol')).toBe(false);
  });
});
