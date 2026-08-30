/**
 * Un anneau de focus se dessine À L'EXTÉRIEUR de l'élément. Dans un conteneur
 * qui découpe, il faut de la place des DEUX côtés.
 *
 * Signalé par Ludo le 30/08/2026 : « le cadre de saisie est tronqué à
 * gauche ». Le conteneur du formulaire de commande portait `pr-2`, une marge
 * à droite seulement. Un champ en `w-full` touchait le bord gauche, et
 * `overflow-y-auto` rend l'axe horizontal découpant lui aussi : l'anneau était
 * rogné.
 *
 * La règle : un conteneur qui découpe et qui contient un élément focusable en
 * pleine largeur doit avoir une marge horizontale SYMÉTRIQUE.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const RACINE = resolve(process.cwd(), 'src');
const SOURCES: string[] = [];
(function collecter(dossier: string) {
  for (const e of readdirSync(dossier, { withFileTypes: true })) {
    const chemin = join(dossier, e.name);
    if (e.isDirectory()) collecter(chemin);
    else if (/\.tsx$/.test(e.name) && !/\.test\.tsx$/.test(e.name)) SOURCES.push(chemin);
  }
})(RACINE);

const court = (f: string) => f.slice(f.lastIndexOf('/src/') + 5);

describe("l'anneau de focus n'est pas rogné par son conteneur", () => {
  it('aucun conteneur qui découpe ne porte une marge horizontale asymétrique', () => {
    // On ne regarde que les conteneurs qui DÉCOUPENT : sans découpe, un anneau
    // qui déborde reste visible.
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      readFileSync(f, 'utf-8')
        .split('\n')
        .forEach((ligne, i) => {
          if (!/\boverflow-(x-|y-)?(auto|scroll|hidden)\b/.test(ligne)) return;
          const gauche = /\b(pl-\d|px-\d|p-\d)\b/.test(ligne);
          const droite = /\b(pr-\d|px-\d|p-\d)\b/.test(ligne);
          if (gauche !== droite) fautifs.push(`${court(f)}:${i + 1}`);
        });
    }
    expect(
      fautifs,
      `${fautifs.length} conteneurs à marge asymétrique : ${fautifs.slice(0, 5).join(', ')}`,
    ).toEqual([]);
  });
});
