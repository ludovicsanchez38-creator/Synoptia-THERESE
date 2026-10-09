/** P-045 : le prédicat frontend suit le backend (_uses_max_completion_tokens) sur des témoins partagés. */
import { describe, expect, it } from 'vitest';

import temoins from './effortOpenAI.temoins.json';
import {
  effortConserveAvecOutils,
  effortTransmisSansOutils,
  familleDeParametres,
  modeleOpenAIRaisonnant,
} from './effortOpenAI';

describe('effortOpenAI (P-045)', () => {
  it.each(Object.entries(temoins.temoins))('%s → famille de paramètres : %s', (modele, attendu) => {
    expect(familleDeParametres(modele)).toBe(attendu);
  });

  it('le transport avec outils est un autre prédicat, Astra compris', () => {
    for (const modele of temoins.transport_avec_outils) {
      expect(effortConserveAvecOutils(modele)).toBe(true);
      expect(familleDeParametres(modele)).toBe(true);
      expect(modeleOpenAIRaisonnant(modele)).toBe(false);
    }
    expect(effortConserveAvecOutils('gpt-6-sol')).toBe(false);
    expect(modeleOpenAIRaisonnant('gpt-6-sol')).toBe(true);
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
