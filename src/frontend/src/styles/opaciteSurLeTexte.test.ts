import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const RACINE = join(__dirname, '..');

function sources(dossier: string, acc: string[] = []): string[] {
  for (const entree of readdirSync(dossier)) {
    if (entree === 'node_modules' || entree.startsWith('.')) continue;
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) sources(chemin, acc);
    else if (/\.tsx?$/.test(entree) && !/\.test\./.test(entree)) acc.push(chemin);
  }
  return acc;
}

describe('aucune opacité sur la couleur de texte secondaire', () => {
  // Mesuré dans l'application lancée le 01/09/2026 : les adresses e-mail de la
  // vue Mémoire ressortaient à 3,09:1. La cause n'est pas la couleur, qui tient
  // largement AA (6,29:1 sur blanc, 5,70:1 sur surface-2), mais l'opacité qui
  // la délave. Le calcul est sans appel : à 70 % elle tombe à 3,23:1, à 60 % à
  // 2,64:1, à 30 % à 1,55:1. AUCUNE opacité ne passe.
  //
  // Un texte secondaire se code par un jeton de couleur, pas par une
  // transparence : la transparence dépend du fond, le jeton non.
  it('text-text-muted n’est jamais posé avec une opacité', () => {
    const fautifs: string[] = [];
    for (const fichier of sources(RACINE)) {
      const contenu = readFileSync(fichier, 'utf-8');
      for (const m of contenu.matchAll(/text-text-muted\/\d{1,3}/g)) {
        fautifs.push(`${fichier.slice(RACINE.length + 1)} : ${m[0]}`);
      }
    }
    expect(fautifs, `${fautifs.length} occurrences — ${fautifs.slice(0, 4).join(' | ')}`).toEqual([]);
  });

  it('le balayage voit bien les fichiers, il ne tourne pas à vide', () => {
    expect(sources(RACINE).length).toBeGreaterThan(200);
  });
});
