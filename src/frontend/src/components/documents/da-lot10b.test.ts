import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const sources = [
  'DocumentCreateModal.tsx',
  'DocumentsList.tsx',
  'DocumentWorkspace.tsx',
  'OutlineTree.tsx',
  'PistesPanel.tsx',
  'SectionEditor.tsx',
].map((nom) => [nom, readFileSync(join(__dirname, nom), 'utf-8')] as const);

describe('Lot 10B DA : atelier documentaire', () => {
  it('ne réintroduit ni grande ombre ni animation de grossissement', () => {
    for (const [nom, source] of sources) {
      expect(source, nom).not.toMatch(/shadow-(?:xl|2xl)/);
      expect(source, nom).not.toMatch(/(?:initial|animate|exit)=\{\{[^}]*scale/);
    }
  });

  it('partage les primitives des formulaires, états et étiquettes', () => {
    const modal = sources.find(([nom]) => nom === 'DocumentCreateModal.tsx')?.[1] ?? '';
    const trame = sources.find(([nom]) => nom === 'OutlineTree.tsx')?.[1] ?? '';
    expect(modal).toContain("from '../ui/FormField'");
    expect(modal).toContain("from '../ui/Select'");
    expect(trame).toContain("from '../ui/Segments'");
    expect(trame).toContain("from '../ui/EtatVide'");
  });

  it('prévoit le repli des actions sous 840 px', () => {
    const sourcesAvecActions = sources
      .filter(([nom]) => ['DocumentCreateModal.tsx', 'DocumentsList.tsx', 'DocumentWorkspace.tsx'].includes(nom))
      .map(([, source]) => source);
    for (const source of sourcesAvecActions) {
      expect(source).toContain('max-[840px]');
    }
  });
});
