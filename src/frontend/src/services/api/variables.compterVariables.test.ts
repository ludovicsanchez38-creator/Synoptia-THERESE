/**
 * B-446 : `(?<!\{)` est une assertion arrière, absente des WebKit antérieurs
 * à Safari 16.4 (cible de build `safari14`). Le module échouait à l'ANALYSE,
 * et ChatInput ne se chargeait pas du tout. Le comptage se fait désormais
 * sans assertion arrière, avec le même résultat.
 */
import { describe, expect, it } from 'vitest';
import { compterVariables, hasVariableTokens } from './variables';

describe('compterVariables (B-446)', () => {
  it('compte les jetons {nom}, y compris accolés', () => {
    expect(compterVariables('{a}{b} et {c_1}')).toBe(3);
  });
  it('ignore une accolade doublée {{nom}}', () => {
    expect(compterVariables('{{a}} {b}')).toBe(1);
    expect(hasVariableTokens('{{a}}')).toBe(false);
  });
  it('ignore les majuscules et les noms trop longs', () => {
    expect(compterVariables('{Nom} {' + 'a'.repeat(33) + '}')).toBe(0);
  });
});
