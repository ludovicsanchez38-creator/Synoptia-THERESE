import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const modales = ['ContactModal.tsx', 'ProjectModal.tsx', 'MemoryPanel.tsx']
  .map((nom) => [nom, readFileSync(join(__dirname, nom), 'utf-8')] as const);

describe('Lot 10B DA : recherche et mémoire', () => {
  it('ne réintroduit ni voile noir, ni grande ombre, ni grossissement', () => {
    for (const [nom, source] of modales) {
      expect(source, nom).not.toMatch(/bg-black\//);
      expect(source, nom).not.toMatch(/shadow-(?:xl|2xl)/);
      expect(source, nom).not.toMatch(/(?:initial|animate|exit)=\{\{[^}]*scale/);
    }
  });

  it('partage les primitives de formulaire dans les deux fiches', () => {
    for (const [nom, source] of modales.filter(([nom]) => nom !== 'MemoryPanel.tsx')) {
      expect(source, nom).toContain("from '../ui/FormField'");
      expect(source, nom).toContain("from '../ui/Input'");
    }
    expect(modales.find(([nom]) => nom === 'ProjectModal.tsx')?.[1]).toContain("from '../ui/Segments'");
  });

  it('prévoit le repli des actions de fiche sous 840 px', () => {
    for (const [nom, source] of modales.filter(([nom]) => nom !== 'MemoryPanel.tsx')) {
      expect(source, nom).toContain('max-[840px]:basis-full');
    }
  });
});
