/**
 * Chantier 4 Variables V1 - garde locale hasVariableTokens (même forme de
 * token que le backend : {nom} minuscules/chiffres/_, {{nom}} = échappement).
 */
import { describe, expect, it } from 'vitest';
import { hasVariableTokens } from './variables';

describe('hasVariableTokens', () => {
  it('détecte un token simple', () => {
    expect(hasVariableTokens('Bonjour {client}')).toBe(true);
  });

  it('ignore un texte sans token', () => {
    expect(hasVariableTokens('Bonjour tout le monde')).toBe(false);
  });

  it('ignore les tokens invalides (majuscules, espaces, tirets)', () => {
    expect(hasVariableTokens('du JSON {Clé} ou {ma var} ou {ma-var}')).toBe(false);
  });

  it("ignore l'échappement {{nom}}", () => {
    expect(hasVariableTokens('un littéral {{client}}')).toBe(false);
  });

  it('détecte un token dans un sujet produire', () => {
    expect(hasVariableTokens('{action: produire docx "liste {courses}"}')).toBe(true);
  });
});
