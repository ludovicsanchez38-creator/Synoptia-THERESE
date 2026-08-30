/**
 * Lot 5 du plan de cohérence graphique (30/08/2026) : plus de couleur brute.
 *
 * 165 couleurs Tailwind brutes servaient de couleur de texte, toutes entre
 * 1,54:1 et 2,44:1 sur le fond clair : des nuances -400 pensées pour un fond
 * sombre, jamais redéclinées quand le thème clair est devenu le défaut. Le
 * correctif de BUG-150 avait fait ce travail pour l'Atelier seulement.
 *
 * Correction due à l'audit : celui-ci annonçait « 102 text-red-400 ». Il y en
 * avait deux dans tout le dépôt. Le vrai volume était ailleurs, en vert, en
 * violet et en cyan.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const RACINE = resolve(process.cwd(), 'src');
const CSS = readFileSync(join(RACINE, 'styles/globals.css'), 'utf-8');

const SOURCES: string[] = [];
(function collecter(dossier: string) {
  for (const e of readdirSync(dossier, { withFileTypes: true })) {
    const chemin = join(dossier, e.name);
    if (e.isDirectory()) collecter(chemin);
    else if (/\.tsx$/.test(e.name) && !/\.test\.tsx$/.test(e.name)) SOURCES.push(chemin);
  }
})(RACINE);

const court = (f: string) => f.slice(f.lastIndexOf('/src/') + 5);

function luminance(hex: string): number {
  const v = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => {
    const c = parseInt(v.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contraste(a: string, b: string): number {
  const [h, l] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (h + 0.05) / (l + 0.05);
}
function bloc(marqueur: string): Record<string, string> {
  const debut = CSS.indexOf(marqueur);
  const ouvre = CSS.indexOf('{', debut);
  let profondeur = 0;
  let fin = ouvre;
  for (let i = ouvre; i < CSS.length; i++) {
    if (CSS[i] === '{') profondeur++;
    else if (CSS[i] === '}' && --profondeur === 0) {
      fin = i;
      break;
    }
  }
  const out: Record<string, string> = {};
  for (const m of CSS.slice(ouvre, fin).matchAll(/--color-([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;/g)) {
    out[m[1]] = m[2];
  }
  return out;
}

const CLAIR = bloc('@theme');
const DOMAINES = ['agenda', 'taches', 'factures', 'prospects'] as const;

describe('lot 5 : plus une seule couleur brute', () => {
  it("aucune couleur Tailwind brute ne sert de couleur de texte", () => {
    const familles =
      'red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose';
    const motif = new RegExp(`\\btext-(?:${familles})-\\d{2,3}\\b`, 'g');
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      for (const m of readFileSync(f, 'utf-8').matchAll(motif)) fautifs.push(`${court(f)} : ${m[0]}`);
    }
    expect(fautifs, `${fautifs.length} couleurs, ex. ${fautifs.slice(0, 3).join(' | ')}`).toEqual([]);
  });

  it.each(DOMAINES)('le domaine %s est lisible sur sa propre teinte', (nom) => {
    const encre = CLAIR[`domaine-${nom}`];
    const teinte = CLAIR[`domaine-${nom}-tint`];
    expect(encre, `--color-domaine-${nom} absent`).toBeTruthy();
    expect(teinte, `--color-domaine-${nom}-tint absent`).toBeTruthy();
    expect(contraste(encre, teinte)).toBeGreaterThanOrEqual(4.5);
    expect(contraste(encre, CLAIR['bg'])).toBeGreaterThanOrEqual(4.5);
  });

  it('les couleurs de domaine sont réellement portées par une surface', () => {
    // Un jeton défini que personne n'utilise, c'est la maladie qu'on soigne.
    const porteurs = SOURCES.filter((f) => /domaine-(agenda|taches|factures|prospects)/.test(readFileSync(f, 'utf-8')));
    expect(porteurs.length, 'aucun composant ne porte les couleurs de domaine').toBeGreaterThanOrEqual(1);
  });
  it("le blanc ne se pose que sur des fonds qui le supportent", () => {
    // Trouvé après les cinq lots : les pilules encre avaient été balayées,
    // pas les autres boutons primaires. Du blanc sur bg-accent-cyan donne
    // 1,81:1, sur bg-green-600 3,30:1, sur bg-purple-500 3,96:1.
    // Seuls les remplissages dont l'encre déclarée est blanche, plus les
    // jetons d'agent et de domaine (tous >= 5:1 en blanc), sont admis.
    const FONDS_ADMIS =
      /bg-(success|warning|error|info)(-fill)?\b|bg-(agent|domaine)-[a-z]+\b|bg-(text-muted|accent)\b/;
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      readFileSync(f, 'utf-8')
        .split('\n')
        .forEach((ligne, i) => {
          if (!/\btext-white\b/.test(ligne)) return;
          const fonds = [...ligne.matchAll(/\bbg-\[?[#\w/.-]+\]?/g)].map((m) => m[0]);
          if (fonds.length === 0) return; // icône blanche sur un fond porté ailleurs
          // Une ligne peut porter plusieurs éléments : on ne peut pas
          // attribuer le text-white à l'un d'eux. La règle est donc « au
          // moins un fond capable de porter du blanc », plus faible mais
          // sans faux positif. Elle attrape le cas réel : une ligne dont le
          // seul fond est bg-accent-cyan, bg-green-600 ou bg-purple-500.
          if (fonds.some((b) => FONDS_ADMIS.test(b))) return;
          fautifs.push(`${court(f)}:${i + 1} → ${fonds.join(' ')}`);
        });
    }
    expect(fautifs, fautifs.slice(0, 4).join(' | ')).toEqual([]);
  });

  it("les couleurs de domaine ne sont pas nommées par un numéro", () => {
    // --k1..--k4 venaient de la maquette de mai. Ils portaient les mêmes
    // quatre couleurs, avec le même défaut de contraste, sous des noms que
    // personne ne peut lire. Un seul jeu, nommé par le domaine.
    const fautifs: string[] = [];
    for (const f of [...SOURCES, join(RACINE, 'styles/globals.css')]) {
      const contenu = readFileSync(f, 'utf-8');
      for (const m of contenu.matchAll(/--k[1-4](bg)?\b/g)) {
        if (/^\s*\/[/*]|^\s*\*/.test(contenu.slice(contenu.lastIndexOf('\n', m.index) + 1, m.index))) continue;
        fautifs.push(`${court(f)} : ${m[0]}`);
      }
    }
    expect(fautifs, fautifs.slice(0, 4).join(' | ')).toEqual([]);
  });

  it("les seules couleurs en dur sont celles qui doivent l'être", () => {
    // Une couleur écrite en hexadécimal dans un className échappe au thème :
    // elle est identique en clair et en sombre. Deux familles le justifient,
    // et seulement deux.
    const LEGITIMES = new Set([
      // Blocs de code : un terminal reste sombre dans les deux thèmes.
      '#0A0F1E', '#0a0f1e', '#131B35', '#1e1e1e', '#B6C7DA',
      // Boutons de fenêtre macOS : ces trois valeurs sont imposées par le système.
      '#FF5F57', '#FEBC2E', '#28C840',
    ]);
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      for (const m of readFileSync(f, 'utf-8').matchAll(
        /\b(?:bg|text|border|ring|from|to|via)-\[(#[0-9A-Fa-f]{3,8})\]/g,
      )) {
        if (!LEGITIMES.has(m[1])) fautifs.push(`${court(f)} : ${m[0]}`);
      }
    }
    expect(fautifs, fautifs.slice(0, 4).join(' | ')).toEqual([]);
  });

  it("la charte Synoptïa ne déborde pas sur THÉRÈSE", () => {
    // Arbitrage de Ludo, 30/08/2026 : THÉRÈSE porte son identité propre.
    // #2451FF est le bleu de la marque Synoptïa.
    const fautifs = SOURCES.filter((f) => /2451FF/i.test(readFileSync(f, 'utf-8')));
    expect(fautifs.map(court)).toEqual([]);
  });
});
