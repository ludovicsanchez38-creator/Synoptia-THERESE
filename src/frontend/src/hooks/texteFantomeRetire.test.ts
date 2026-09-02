/**
 * B-113 : le texte fantôme était désarmé par une constante, son code restait
 * en place.
 *
 * `useGhostText` posait `GHOST_TEXT_ENABLED = false` et sortait aussitôt,
 * parce que l'endpoint `POST /api/chat/complete` n'existe pas côté backend.
 * Le hook continuait pourtant d'être monté par le composeur, et quatre
 * branches de ChatInput dépendaient d'une suggestion qui ne pouvait plus
 * jamais être renseignée : le raccourci Tab, l'Échap concurrent de la
 * fermeture du menu, la superposition grisée et l'astuce « Tab accepter ».
 *
 * Du code inatteignable ne se relit pas, ne se teste pas, et se réveille mal :
 * le prochain qui remettra la constante à `true` rebranchera quatre chemins
 * que personne n'a exercés depuis juillet, contre une route absente.
 *
 * Ce test refuse que la trace revienne. Rebrancher la fonctionnalité, ce sera
 * l'écrire avec sa route et ses tests, pas rallumer un interrupteur.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';

const ici = dirname(fileURLToPath(import.meta.url));
const racineSrc = resolve(ici, '..');
const ceFichier = resolve(ici, 'texteFantomeRetire.test.ts');

const MOTIFS = [/useGhostText/, /GHOST_TEXT_ENABLED/, /ghostSuggestion/];

function fichiers(dossier: string, acc: string[] = []): string[] {
  for (const entree of readdirSync(dossier)) {
    if (entree === 'node_modules' || entree === 'dist') continue;
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) {
      fichiers(chemin, acc);
      continue;
    }
    if (!/\.(tsx|ts)$/.test(entree)) continue;
    if (chemin === ceFichier) continue;
    acc.push(chemin);
  }
  return acc;
}

describe('B-113 - le texte fantôme ne laisse aucune trace', () => {
  it('parcourt bien tout le code source', () => {
    expect(fichiers(racineSrc).length).toBeGreaterThan(300);
  });

  it('aucun fichier ne référence encore le hook désarmé', () => {
    const restes: string[] = [];
    for (const fichier of fichiers(racineSrc)) {
      const contenu = readFileSync(fichier, 'utf-8');
      for (const motif of MOTIFS) {
        if (motif.test(contenu)) {
          restes.push(`${fichier.slice(racineSrc.length + 1)} : ${motif.source}`);
        }
      }
    }
    expect(
      restes,
      'le texte fantôme a été retiré, mais ces fichiers le mentionnent ' +
        `encore :\n${restes.join('\n')}`,
    ).toEqual([]);
  });
});
