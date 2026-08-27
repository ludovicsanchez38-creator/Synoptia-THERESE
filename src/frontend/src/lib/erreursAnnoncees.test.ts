/**
 * Un échec silencieux n'existe que pour l'œil.
 *
 * Socle P3 du plan, volet « erreur ». Le bandeau qui s'affiche après une
 * action refusée - enregistrement impossible, connexion perdue - entrait dans
 * le DOM sans rien annoncer : un lecteur d'écran ne le lit pas, et la personne
 * croit son enregistrement passé.
 *
 * La règle balaie TOUTE l'application plutôt qu'une liste de fichiers : une
 * liste se périme au premier écran ajouté, et c'est exactement ainsi que la
 * dérive revient. Elle ne vise que le bandeau conditionné à un état d'erreur ;
 * une variante de style rouge (un bouton) n'est pas un message.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

const RACINE = path.join(__dirname, '..');
const CONDITION = /\{\s*(error|erreur|\w*Error)\s*&&\s*\(?/;
const FOND_ERREUR = /bg-error\/10|bg-red-500\/10/;

function fichiersSources(dossier: string): string[] {
  return readdirSync(dossier).flatMap((entree) => {
    const complet = path.join(dossier, entree);
    if (statSync(complet).isDirectory()) return fichiersSources(complet);
    if (!entree.endsWith('.tsx')) return [];
    if (entree.includes('.test.') || entree.includes(' 2.')) return [];
    return [complet];
  });
}

/** Les bandeaux d'erreur muets, en « chemin:ligne ». */
function bandeauxMuets(): string[] {
  const muets: string[] = [];
  for (const fichier of fichiersSources(path.join(RACINE, 'components'))) {
    const lignes = readFileSync(fichier, 'utf8').split('\n');
    lignes.forEach((ligne, i) => {
      if (!CONDITION.test(ligne)) return;
      for (let j = i + 1; j < Math.min(i + 3, lignes.length); j += 1) {
        if (!FOND_ERREUR.test(lignes[j])) continue;
        if (!/role="alert"|aria-live=/.test(lignes[j])) {
          muets.push(`${path.relative(RACINE, fichier)}:${j + 1}`);
        }
        break;
      }
    });
  }
  return muets;
}

describe('Une erreur affichée après une action est annoncée', () => {
  it('aucun bandeau d’erreur n’entre muet dans la page', () => {
    expect(bandeauxMuets()).toEqual([]);
  });

  it('la règle trouve bien des bandeaux à surveiller (sinon elle ne prouve rien)', () => {
    const annonces = fichiersSources(path.join(RACINE, 'components')).filter((f) =>
      /role="alert"/.test(readFileSync(f, 'utf8')),
    );
    expect(annonces.length).toBeGreaterThan(10);
  });
});
