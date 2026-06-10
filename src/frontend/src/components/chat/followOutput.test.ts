/**
 * US-010 : le scroll respecte la position de l'utilisateur.
 *
 * Avant : MessageList faisait scrollIntoView à CHAQUE changement de contenu,
 * même si l'utilisateur avait remonté la conversation pour lire → impossible
 * de lire pendant que Thérèse écrit.
 */
import { describe, expect, it } from 'vitest';
import { computeFollowOutput } from './followOutput';

describe('computeFollowOutput (US-010)', () => {
  it('suit le flux quand l utilisateur est en bas (streaming → auto)', () => {
    expect(computeFollowOutput(true, true)).toBe('auto');
  });

  it('suit en douceur quand on est en bas hors streaming', () => {
    expect(computeFollowOutput(true, false)).toBe('smooth');
  });

  it('NE scrolle PAS si l utilisateur a remonté la conversation', () => {
    expect(computeFollowOutput(false, true)).toBe(false);
    expect(computeFollowOutput(false, false)).toBe(false);
  });
});
