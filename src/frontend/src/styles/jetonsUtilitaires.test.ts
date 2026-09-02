/**
 * B-109 : un jeton de couleur déclaré hors du bloc @theme ne produit AUCUNE
 * classe utilitaire.
 *
 * Tailwind 4 ne fabrique ses utilitaires que depuis @theme. `--color-instant`
 * vivait dans `:root` : la ligne de l'heure courante de l'agenda portait donc
 * `bg-instant`, une classe qui n'existait dans aucune feuille compilée, et le
 * repère temporel était purement et simplement invisible. Le CSS de
 * production ne contenait pas une occurrence de `.bg-instant`, quand le témoin
 * `.bg-domaine-agenda-tint`, déclaré dans @theme, en comptait une.
 *
 * Le défaut est silencieux par nature : rien ne casse, rien n'avertit, une
 * div s'affiche sans couleur. Ce test lit la feuille de style et le code, et
 * refuse qu'une classe utilitaire s'appuie sur un jeton que Tailwind ne verra
 * jamais.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';

const ici = dirname(fileURLToPath(import.meta.url));
const racineSrc = resolve(ici, '..');

/** Préfixes Tailwind qui consomment un jeton `--color-*`. */
const PREFIXES = [
  'bg',
  'text',
  'border',
  'ring',
  'fill',
  'stroke',
  'from',
  'via',
  'to',
  'outline',
  'divide',
  'accent',
  'caret',
  'decoration',
  'placeholder',
  'shadow',
];

/** Retire les commentaires CSS pour ne pas lire une déclaration commentée. */
function sansCommentaires(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, '');
}

/** Contenu du bloc `@theme { ... }`, par appariement d'accolades. */
function blocTheme(css: string): string {
  const debut = css.indexOf('@theme');
  if (debut === -1) return '';
  const ouvrante = css.indexOf('{', debut);
  if (ouvrante === -1) return '';
  let profondeur = 0;
  for (let i = ouvrante; i < css.length; i++) {
    if (css[i] === '{') profondeur++;
    else if (css[i] === '}') {
      profondeur--;
      if (profondeur === 0) return css.slice(ouvrante + 1, i);
    }
  }
  return '';
}

function nomsDeJetons(css: string): Set<string> {
  const noms = new Set<string>();
  for (const m of css.matchAll(/--color-([a-z0-9-]+)\s*:/g)) noms.add(m[1]);
  return noms;
}

function fichiersSources(dossier: string, acc: string[] = []): string[] {
  for (const entree of readdirSync(dossier)) {
    if (entree === 'node_modules' || entree === 'dist') continue;
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) {
      fichiersSources(chemin, acc);
      continue;
    }
    if (!/\.(tsx|ts)$/.test(entree)) continue;
    if (/\.(test|spec)\.(tsx|ts)$/.test(entree)) continue;
    acc.push(chemin);
  }
  return acc;
}

const css = sansCommentaires(readFileSync(resolve(ici, 'globals.css'), 'utf-8'));
const jetonsDeclares = nomsDeJetons(css);
const jetonsDansTheme = nomsDeJetons(blocTheme(css));

describe('B-109 - une classe utilitaire exige un jeton dans @theme', () => {
  it('lit bien la feuille de style et son bloc @theme', () => {
    expect(jetonsDansTheme.size).toBeGreaterThan(20);
    expect(jetonsDeclares.size).toBeGreaterThanOrEqual(jetonsDansTheme.size);
    // Témoin de la fiche de bug : ce jeton-là a toujours été dans @theme.
    expect(jetonsDansTheme.has('domaine-agenda-tint')).toBe(true);
  });

  it('aucune classe de couleur ne repose sur un jeton hors @theme', () => {
    const fautifs: string[] = [];

    for (const jeton of jetonsDeclares) {
      if (jetonsDansTheme.has(jeton)) continue;
      const motif = new RegExp(
        `(?<![\\w-])(${PREFIXES.join('|')})-${jeton}(?![\\w-])`,
      );
      for (const fichier of fichiersSources(racineSrc)) {
        const contenu = readFileSync(fichier, 'utf-8');
        const trouve = contenu.match(motif);
        if (trouve) {
          fautifs.push(
            `${fichier.slice(racineSrc.length + 1)} utilise « ${trouve[0]} » ` +
              `mais --color-${jeton} est déclaré hors de @theme : Tailwind ne ` +
              `génère aucune règle, l'élément s'affiche sans couleur`,
          );
        }
      }
    }

    expect(fautifs, fautifs.join('\n')).toEqual([]);
  });
});
