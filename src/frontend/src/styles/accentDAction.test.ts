/**
 * Lot 2 du plan de cohérence graphique (30/08/2026) : une seule langue d'action.
 *
 * La DA « Équilibre » validée en mai 2026 donne l'accent d'action :
 * --color-accent-fill (#22D3EE) sur --color-accent-ink (#06121F), soit 10,43:1.
 * Ses jetons étaient déjà dans globals.css. Ils n'étaient consommés que par
 * 5 fichiers, pendant que 56 éléments écrivaient une pilule encre à la main et
 * qu'un quatrième langage (« brutaliste éditorial ») vivait dans Button.tsx.
 *
 * Ces tests interdisent le retour des trois.
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
    else if (/\.tsx?$/.test(e.name) && !/\.test\.tsx?$/.test(e.name)) SOURCES.push(chemin);
  }
})(RACINE);

const court = (f: string) => f.slice(f.lastIndexOf('/src/') + 5);

describe("lot 2 : l'action porte l'accent, pas l'encre", () => {
  it("aucun élément ne peint une action en encre sur texte blanc", () => {
    // Détection à la ligne : les className de ce projet tiennent sur une ligne.
    // Un className réparti sur plusieurs lignes échapperait au test ; c'est une
    // limite assumée, pas un oubli.
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      readFileSync(f, 'utf-8')
        .split('\n')
        .forEach((ligne, i) => {
          if (/\bbg-text\b(?!-)/.test(ligne) && /\btext-white\b/.test(ligne)) {
            fautifs.push(`${court(f)}:${i + 1}`);
          }
        });
    }
    expect(fautifs, `${fautifs.length} pilules encre : ${fautifs.slice(0, 4).join(', ')}`).toEqual(
      [],
    );
  });

  it("le langage « brutaliste éditorial » a disparu", () => {
    // Quatrième direction artistique du projet, à côté de la DA, de
    // RULES-DESIGN.md et de l'écran de démarrage. Bordure 2 px et ombre dure,
    // incompatibles avec l'ombre bleutée douce de la DA.
    expect(CSS).not.toContain('.btn-brutal');
    for (const f of SOURCES) {
      expect(readFileSync(f, 'utf-8'), `${court(f)} porte encore btn-brutal`).not.toContain(
        'btn-brutal',
      );
    }
  });

  it("le correctif qui rattrapait la pilule en thème sombre n'a plus lieu d'être", () => {
    // globals.css repeignait le texte blanc des pilules encre en thème sombre,
    // parce qu'une pilule encre sur fond sombre est invisible. L'accent rend
    // ce rattrapage inutile.
    expect(CSS).not.toContain('.bg-text.text-white');
  });

  it("l'accent d'action est réellement consommé", () => {
    // Un jeton défini que personne n'utilise est la maladie qu'on soigne ici :
    // ce test échoue si on « répare » en supprimant les boutons.
    const fichiers = SOURCES.filter((f) => /bg-accent-fill/.test(readFileSync(f, 'utf-8')));
    expect(fichiers.length, `seulement ${fichiers.length} fichiers`).toBeGreaterThanOrEqual(20);
  });
  it("aucune ombre dure ne subsiste", () => {
    // Signature du brutalisme : un décalage sans flou. La DA « Équilibre »
    // pose une ombre douce bleutée (--shadow-card), la « Signature » une
    // ombre noire portée. Les deux ont un flou.
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      for (const m of readFileSync(f, 'utf-8').matchAll(/shadow-\[\d+px_\d+px_0_/g)) {
        fautifs.push(`${court(f)} : ${m[0]}`);
      }
    }
    expect(fautifs, fautifs.slice(0, 3).join(' | ')).toEqual([]);
  });
});
