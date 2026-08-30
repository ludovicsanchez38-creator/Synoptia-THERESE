/**
 * THÉRÈSE doit avoir sa police, pas celle du système.
 *
 * Constat du 30/08/2026 : globals.css déclarait `'Inter', system-ui, …` alors
 * qu'aucune police n'était embarquée (zéro @font-face, zéro .woff2, zéro
 * @fontsource). L'application empruntait donc SF Pro sur macOS et Segoe UI sur
 * Windows, c'est-à-dire la police de Claude Desktop et de ChatGPT.
 *
 * Ces tests interdisent le retour de cet état. Ils lisent les fichiers du
 * dépôt, parce que le défaut n'est pas observable au rendu jsdom : jsdom
 * n'échoue jamais à « charger » une police, il se rabat en silence.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const racineFront = join(__dirname, '..', '..');
const lire = (chemin: string) => readFileSync(join(racineFront, chemin), 'utf-8');

describe('les polices sont embarquées, pas empruntées au système', () => {
  it('le point d’entrée charge réellement les fichiers de police', () => {
    const entree = lire('src/main.tsx') + lire('src/styles/globals.css');
    expect(
      /@fontsource/.test(entree) || /@font-face/.test(entree),
      "aucune police n'est chargée : l'application prendra celle du système",
    ).toBe(true);
  });

  it('les paquets de police sont des dépendances, pas un appel réseau', () => {
    const pkg = JSON.parse(lire('package.json')) as {
      dependencies?: Record<string, string>;
    };
    const deps = Object.keys(pkg.dependencies ?? {});
    expect(deps.some((d) => d.includes('inter'))).toBe(true);
    expect(deps.some((d) => d.includes('jakarta'))).toBe(true);
  });

  it('aucune police n’est appelée sur le réseau (l’application marche hors ligne)', () => {
    const sources = lire('index.html') + lire('src/styles/globals.css');
    expect(/fonts\.(googleapis|gstatic)\.com/.test(sources)).toBe(false);
  });

  it('la pile de texte commence par Inter, celle des titres par Plus Jakarta Sans', () => {
    const css = lire('src/styles/globals.css');
    expect(css).toMatch(/--font-family-sans:\s*'Inter'/);
    expect(css).toMatch(/--font-family-display:\s*'Plus Jakarta Sans'/);
  });

  it('l’écran de démarrage n’ouvre pas sur la police du système', () => {
    // index.html est la toute première image du produit : s'il déclare
    // -apple-system en tête de pile, le lancement ressemble à n'importe
    // quelle application macOS, quel que soit le reste du travail.
    const html = lire('index.html');
    const piles = [...html.matchAll(/font-family:\s*([^;}"']+)/g)].map((m) =>
      m[1].trim().replace(/^["']|["']$/g, ''),
    );
    expect(piles.length, 'aucune pile de police trouvée dans index.html').toBeGreaterThan(0);
    for (const pile of piles) {
      const premiere = pile.split(',')[0].trim().replace(/["']/g, '');
      expect(
        /^(-apple-system|system-ui|BlinkMacSystemFont|sans-serif)$/i.test(premiere),
        `l'écran de démarrage ouvre sur « ${premiere} », la police du système`,
      ).toBe(false);
    }
  });
  it('les copies servies au démarrage sont conformes au paquet', () => {
    // public/fonts/ duplique deux fichiers de node_modules. Une copie qui
    // dérive après une montée de version donnerait un splash dans une police
    // et une application dans une autre, sans que rien n'échoue.
    const copies: [string, string][] = [
      [
        'public/fonts/plus-jakarta-sans-latin-700-normal.woff2',
        'node_modules/@fontsource/plus-jakarta-sans/files/plus-jakarta-sans-latin-700-normal.woff2',
      ],
      [
        'public/fonts/inter-latin-500-normal.woff2',
        'node_modules/@fontsource/inter/files/inter-latin-500-normal.woff2',
      ],
    ];
    for (const [copie, source] of copies) {
      expect(
        readFileSync(join(racineFront, copie)).equals(readFileSync(join(racineFront, source))),
        `${copie} a dérivé de ${source}`,
      ).toBe(true);
    }
  });
});
