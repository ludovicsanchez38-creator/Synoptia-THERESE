/**
 * DA « Application affinée », lot 1 (10/09/2026) : la cascade.
 *
 * Tailwind 4 ne génère une utilitaire que depuis un jeton du bloc `@theme`
 * (B-109 : un jeton posé dans `:root` ne produit rien, la classe existe dans
 * le JSX et n'a aucune règle). Et une règle écrite hors `@layer` bat toute
 * utilitaire : les jumeaux `h1,h2,h3` et `:focus-visible` hors couche
 * rendaient mortes les règles DA posées en `@layer base`.
 *
 * Ce test lit la source, pas un rendu : jsdom ne calcule ni une largeur
 * issue de `@theme` ni une couche. La largeur réelle se mesure en recette.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const CSS = readFileSync(join(__dirname, 'globals.css'), 'utf-8');

function blocTheme(): string {
  const debut = CSS.indexOf('@theme {');
  const fin = CSS.indexOf('\n}', debut);
  return CSS.slice(debut, fin);
}

/** Le CSS sans ses blocs `@layer … { … }` : ce qui reste est hors couche. */
function horsCouche(): string {
  return CSS.replace(/@layer\s+\w+\s*\{[\s\S]*?\n\}/g, '');
}

function blocLayerBase(): string {
  const m = CSS.match(/@layer base\s*\{([\s\S]*?)\n\}/);
  return m ? m[1] : '';
}

describe('DA lot 1 : les jetons vivent dans @theme', () => {
  it('la colonne de 56 rem et la police éditoriale sont des jetons Tailwind', () => {
    const theme = blocTheme();
    expect(theme).toMatch(/--container-colonne:\s*56rem/);
    expect(theme).toMatch(/--font-editorial:/);
  });

  it('les quatre teintes sémantiques sont promues dans @theme (B-109)', () => {
    const theme = blocTheme();
    for (const ton of ['error', 'success', 'warning', 'info']) {
      expect(theme, `--color-${ton}-tint absent de @theme`).toMatch(new RegExp(`--color-${ton}-tint:\\s*#[0-9A-Fa-f]{6}`));
    }
  });
});

describe('DA lot 1 : les règles d’élément vivent en @layer base', () => {
  it('aucun jumeau h1/h2/h3 ni :focus-visible ne reste hors couche', () => {
    const reste = horsCouche();
    expect(reste).not.toMatch(/\nh1,\s*\nh2,\s*\nh3\s*\{/);
    // Le bloc contraste élevé (`[data-high-contrast="true"] :focus-visible`)
    // est un thème, il reste ; c'est le sélecteur nu qui ne doit plus exister.
    expect(reste).not.toMatch(/\n:focus-visible\s*\{/);
  });

  it('la couche base porte les titres, le corps de texte et le focus de la DA', () => {
    const base = blocLayerBase();
    expect(base).toMatch(/h1\s*\{[^}]*font-size:\s*1\.625rem[^}]*font-weight:\s*800/s);
    expect(base).toMatch(/h2\s*\{[^}]*font-size:\s*1\.1875rem/s);
    expect(base).toMatch(/h3\s*\{[^}]*font-size:\s*1rem/s);
    expect(base).toMatch(/body\s*\{[^}]*font:\s*400\s+0?\.875rem\/1\.5\s+var\(--font-family-sans\)/s);
    expect(base).toMatch(/:focus-visible\s*\{[^}]*outline:\s*3px solid var\(--color-ring\)/s);
  });

  it('html{font-size:16px} de la maquette n’est pas copié : la préférence de taille reste maîtresse', () => {
    expect(CSS).not.toMatch(/\nhtml\s*\{[^}]*font-size:\s*16px/s);
  });
});

describe('DA lot 1 : ce qui est retiré et ce qui est ajouté', () => {
  it('btn-da et card-brutal (DA « Équilibre » du 30/08) n’existent plus', () => {
    expect(CSS).not.toContain('.btn-da');
    expect(CSS).not.toContain('.card-brutal');
  });

  it('en contraste élevé, une étiquette abandonne sa teinte pour une bordure d’encre', () => {
    expect(horsCouche()).toMatch(/\[data-high-contrast="true"\]\s*\[data-etiquette\]\s*\{[^}]*background:\s*transparent[^}]*border:\s*1px solid currentColor/s);
  });
});
