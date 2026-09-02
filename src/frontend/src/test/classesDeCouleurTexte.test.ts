/**
 * B-091 : une classe de couleur de texte doit correspondre à un jeton défini.
 *
 * Sept usages de `text-muted` peignaient avec un jeton qui n'existe pas — seul
 * `--color-text-muted` est défini, donc seule la classe `text-text-muted` a une
 * couleur. Ces textes n'en avaient aucune. Les usages ont été corrigés le
 * 01/09/2026 (commit ba0465a6) ; la porte manquait.
 *
 * Périmètre : la famille `text-*` seule, celle du défaut. `bg-*` et `border-*`
 * mêlent encore des couleurs Tailwind brutes à la charte : les fermer demande
 * une décision de design, pas une garde.
 *
 * Piège rencontré lors du correctif d'origine, conservé ici : dans
 * `a11y.test.tsx`, `text-muted` désigne un NOM DE JETON, pas une classe. Les
 * fichiers de test sont donc hors du balayage.
 */
import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { resolve } from 'node:path';

const SOURCES = resolve(process.cwd(), 'src');
const CSS = readFileSync(resolve(SOURCES, 'styles/globals.css'), 'utf-8');

/** Les jetons de couleur de la charte, quel que soit le thème qui les pose. */
const JETONS = new Set(
  [...CSS.matchAll(/--color-([a-z0-9-]+)\s*:/g)].map((m) => m[1]),
);

/** Utilitaires Tailwind de la famille `text-*` qui ne sont PAS des couleurs
 *  (taille, alignement, mot-clé CSS). */
const NON_COULEURS = new Set([
  'xs', 'sm', 'base', 'lg', 'xl',
  'left', 'center', 'right', 'justify', 'start', 'end',
  'transparent', 'current', 'inherit', 'nowrap', 'wrap', 'balance', 'pretty',
  'ellipsis', 'clip',
]);

function sources(): string[] {
  const trouves: string[] = [];
  const parcourir = (dossier: string) => {
    for (const entree of readdirSync(dossier)) {
      if (entree === 'node_modules' || entree.startsWith('.')) continue;
      const chemin = resolve(dossier, entree);
      if (statSync(chemin).isDirectory()) parcourir(chemin);
      else if (/\.(ts|tsx)$/.test(entree) && !/\.(test|spec)\.(ts|tsx)$/.test(entree)) {
        trouves.push(chemin);
      }
    }
  };
  parcourir(SOURCES);
  return trouves;
}

describe('B-091 : les classes text-* désignent un jeton existant', () => {
  it('la charte définit bien des jetons de couleur', () => {
    expect(JETONS.size).toBeGreaterThan(10);
    expect(JETONS.has('text-muted')).toBe(true);
  });

  it('aucune classe text-* ne peint avec un jeton absent de la charte', () => {
    const fautes: string[] = [];
    for (const chemin of sources()) {
      const texte = readFileSync(chemin, 'utf-8');
      texte.split('\n').forEach((ligne, index) => {
        for (const m of ligne.matchAll(/(?<![\w-])text-([a-z][a-z0-9-]*)(?![\w-])/g)) {
          const suffixe = m[1];
          if (JETONS.has(suffixe) || NON_COULEURS.has(suffixe)) continue;
          fautes.push(
            `${chemin.slice(SOURCES.length + 1)}:${index + 1} → text-${suffixe}`,
          );
        }
      });
    }
    expect(fautes, `classes sans jeton :\n${fautes.join('\n')}`).toEqual([]);
  });
});
