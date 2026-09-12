import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const browser = readFileSync(join(__dirname, 'FileBrowser.tsx'), 'utf-8');
const depot = readFileSync(join(__dirname, 'DropZone.tsx'), 'utf-8');

describe('Lot 10B DA : indexation locale', () => {
  it('emploie les primitives communes pour la recherche et les états', () => {
    expect(browser).toContain("from '../ui/Input'");
    expect(browser).toContain("from '../ui/Alerte'");
    expect(browser).toContain("from '../ui/EtatVide'");
    expect(browser).toContain("from '../ui/Etiquette'");
  });

  it('ne réintroduit ni grande ombre ni animation de grossissement', () => {
    for (const source of [browser, depot]) {
      expect(source).not.toMatch(/shadow-(?:xl|2xl)/);
      expect(source).not.toMatch(/(?:initial|animate|exit)=\{\{[^}]*scale/);
    }
  });

  it('fait passer les actions du navigateur à la ligne sous 840 px', () => {
    expect(browser).toContain('max-[840px]:basis-full');
  });
});
