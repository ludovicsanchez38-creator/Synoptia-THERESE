/**
 * B-770 (cycle 9) : le libellé de base légale « Interet legitime » s'affichait
 * sans accents. Les libellés d'interface portent leurs accents.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

describe('MemoryPanel - B-770, libellés RGPD accentués', () => {
  it('ne contient ni « Interet » ni « legitime » sans accent', () => {
    const source = readFileSync(resolve(__dirname, 'MemoryPanel.tsx'), 'utf8');
    expect(source).not.toMatch(/'Interet\b|\blegitime'/);
    expect(source).toMatch(/Intérêt légitime/);
  });
});
