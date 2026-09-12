import { readFileSync, readdirSync } from 'node:fs';
import { basename, dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

const componentsDir = dirname(dirname(fileURLToPath(import.meta.url)));
const scopedDirs = ['atelier', 'guided', 'actions'].map((name) => join(componentsDir, name));

const sources = scopedDirs.flatMap((dir) =>
  readdirSync(dir)
    .filter((name) => name.endsWith('.tsx') && !name.includes('.test.'))
    .map((name) => ({
      path: join(dir, name),
      name: relative(componentsDir, join(dir, name)),
      source: readFileSync(join(dir, name), 'utf8'),
    })),
);

const readComponent = (folder: string, name: string) =>
  readFileSync(join(componentsDir, folder, name), 'utf8');

describe('P-090 lot 10C : contrat DA des écrans agents', () => {
  it('n’emploie plus de couleurs, dégradés, ombres fortes ou effets de scale en dur', () => {
    const interdits: Array<[string, RegExp]> = [
      ['couleur hexadécimale', /#[\da-fA-F]{6}(?:[\da-fA-F]{2})?\b/],
      ['couleur rgb ou color-mix', /\brgba?\(|\bhsla?\(|\bcolor-mix\(/],
      ['dégradé', /\b(?:bg-)?gradient-/],
      ['ombre forte ou arbitraire', /\bshadow-(?:xl|2xl|agent[^\s'"]*|\[[^\]]+\])/],
      ['effet de scale', /\bscale(?::|-[\d[])/],
      ['transition globale', /\btransition-all\b/],
    ];

    const violations = sources.flatMap(({ name, source }) =>
      interdits
        .filter(([, pattern]) => pattern.test(source))
        .map(([label]) => `${name}: ${label}`),
    );

    expect(violations).toEqual([]);
  });

  it('utilise les primitives UI pour les boutons et les champs éditables', () => {
    const violations = sources.flatMap(({ name, source }) => {
      const found: string[] = [];
      if (/<(?:motion\.)?button\b/.test(source)) found.push('bouton brut');
      if (/<(?:input|textarea)\b/.test(source)) found.push('champ brut');
      if (/<Button\b[^>]*\btext-xs\b/.test(source)) found.push('libellé interactif en 12 px');
      return found.map((label) => `${name}: ${label}`);
    });

    expect(violations).toEqual([]);
  });

  it('prévoit le retour à la ligne des groupes d’actions étroits', () => {
    const groupes = [
      ['atelier', 'AtelierPanel.tsx'],
      ['atelier', 'AgentSession.tsx'],
      ['atelier', 'CodeReviewPanel.tsx'],
      ['atelier', 'NewTaskDialog.tsx'],
      ['guided', 'CreateCommandForm.tsx'],
      ['guided', 'DynamicSkillForm.tsx'],
      ['guided', 'SkillPromptPanel.tsx'],
      ['guided', 'ImageGenerationPanel.tsx'],
      ['guided', 'SkillExecutionPanel.tsx'],
      ['actions', 'ActionPanel.tsx'],
    ] as const;

    const sansWrap = groupes
      .filter(([folder, name]) => !/\bflex\s+flex-wrap\b/.test(readComponent(folder, name)))
      .map(([, name]) => basename(name));

    expect(sansWrap).toEqual([]);
  });

  it('conserve les deux commandes de session comme boutons frères', () => {
    const source = readComponent('atelier', 'SessionList.tsx');
    expect(source).not.toMatch(/<motion\.button\b/);
    expect(source).toMatch(/aria-label=\{`Ouvrir la session/);
    expect(source).toContain('aria-label="Annuler cette session"');
    expect(source).toContain('aria-label="Relancer cette tache"');
  });
});
