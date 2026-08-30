/**
 * Lot 4 du plan de cohérence graphique (30/08/2026) : le plancher.
 *
 * L'audit a relevé une application où l'essentiel du texte vit à 12 px, une
 * taille faite pour les métadonnées, avec 50 endroits encore en dessous
 * (jusqu'à 9 px) et sept tailles écrites en pixels.
 *
 * Deux règles, les seules qu'une machine puisse vérifier sans juger du sens
 * de chaque phrase :
 *   - rien ne descend sous 12 px ;
 *   - ce qui se clique est à 14 px au moins.
 * Le tri « métadonnée ou pas » entre 12 et 14 px reste un travail humain.
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

describe('lot 4 : le plancher typographique', () => {
  it('aucune taille de texte n’est écrite en pixels', () => {
    // Une taille en pixels échappe au thème, au zoom et à toute revue : elle
    // n'est comparable à rien.
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      for (const m of readFileSync(f, 'utf-8').matchAll(/\btext-\[[\d.]+px\]/g)) {
        fautifs.push(`${court(f)} : ${m[0]}`);
      }
    }
    expect(fautifs, `${fautifs.length} tailles, ex. ${fautifs.slice(0, 3).join(' | ')}`).toEqual([]);
  });

  it('rien ne descend sous 12 px', () => {
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      const contenu = readFileSync(f, 'utf-8');
      for (const m of contenu.matchAll(/\btext-\[([\d.]+)px\]/g)) {
        if (parseFloat(m[1]) < 12) fautifs.push(`${court(f)} : ${m[0]}`);
      }
      if (/\btext-2xs\b/.test(contenu)) fautifs.push(`${court(f)} : text-2xs`);
    }
    expect(fautifs, fautifs.slice(0, 4).join(' | ')).toEqual([]);
  });

  it('ce qui se clique est à 14 px au moins', () => {
    // Lecture de la BALISE entière, pas de la ligne. La revue adverse du
    // 30/08/2026 a montré que la détection à la ligne rate tous les
    // className répartis sur plusieurs lignes ou construits dans un tableau
    // cn(...) : « Réessayer » du brief et les boutons de l'Atelier étaient
    // restés à 12 px alors que le test annonçait la règle satisfaite.
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      const contenu = readFileSync(f, 'utf-8');
      for (const m of contenu.matchAll(/<button\b/g)) {
        // La balise ouvrante s'arrête au premier > hors accolades JSX.
        let i = m.index + 7;
        let profondeur = 0;
        for (; i < contenu.length; i++) {
          const ch = contenu[i];
          if (ch === '{') profondeur++;
          else if (ch === '}') profondeur--;
          else if (ch === '>' && profondeur === 0) break;
        }
        const balise = contenu.slice(m.index, i);
        if (/\btext-xs\b/.test(balise)) {
          const ligne = contenu.slice(0, m.index).split('\n').length;
          fautifs.push(`${court(f)}:${ligne}`);
        }
      }
    }
    expect(
      fautifs,
      `${fautifs.length} boutons sous le plancher : ${fautifs.slice(0, 5).join(', ')}`,
    ).toEqual([]);
  });
});
