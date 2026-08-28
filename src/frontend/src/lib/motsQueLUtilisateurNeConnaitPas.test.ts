/**
 * E — purge du jargon, dernière tâche du chantier nommage.
 *
 * Campagne dix personas, persona 08 (responsable administratif) :
 *
 *   « Sur le côté, des petits dessins sans nom. Je n'ose pas. Je cherche
 *     Annuler : il n'y est pas. J'ai peur de casser quelque chose. »
 *
 * Le contrôle qu'il cherchait existait : une icône, sans nom visible, dont le
 * nom accessible était « Fermer le canevas ». Deux obstacles d'un coup - un
 * mot de métier logiciel, et aucune étiquette lisible.
 *
 * L'artisan a relevé le même mot dans sa liste de jargon. « Canevas » désigne
 * un concept d'interface que personne n'a demandé à connaître : ce que
 * l'utilisateur voit, c'est un panneau de travail qui s'ouvre à côté de la
 * conversation.
 *
 * Ce gate ne liste pas des synonymes acceptables - il interdit le mot dans
 * les chaînes que l'utilisateur LIT ou ENTEND. Les commentaires de code, les
 * noms de fichiers et les identifiants techniques restent libres : renommer
 * `ConversationCanvasPrototype` n'apporterait rien à personne.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const RACINE = join(__dirname, '..');

/** Mots de métier logiciel qu'aucun persona n'a employés spontanément. */
const MOTS_INTERDITS = [/canevas/i, /référentiel/i];

/** Les chaînes que l'utilisateur lit ou entend, pas le code autour. */
const ATTRIBUTS_VISIBLES = /(?:aria-label|title|placeholder|alt)=\{?["'`]([^"'`]+)["'`]/g;

function fichiersSources(dossier: string): string[] {
  return readdirSync(dossier).flatMap((entree) => {
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) return fichiersSources(chemin);
    if (!/\.tsx?$/.test(entree) || /\.test\./.test(entree)) return [];
    return [chemin];
  });
}

/** Retire commentaires et imports : seul le texte rendu compte. */
function texteRendu(source: string): string {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/^\s*\/\/.*$/gm, '')
    .replace(/^import .*$/gm, '');
}

describe("Les mots que l'utilisateur ne connaît pas", () => {
  const sources = fichiersSources(RACINE).map((chemin) => ({
    chemin: chemin.slice(RACINE.length + 1),
    texte: texteRendu(readFileSync(chemin, 'utf-8')),
  }));

  it('aucun nom accessible ni infobulle ne porte de jargon', () => {
    const fautes: string[] = [];
    for (const { chemin, texte } of sources) {
      for (const [, valeur] of texte.matchAll(ATTRIBUTS_VISIBLES)) {
        if (MOTS_INTERDITS.some((mot) => mot.test(valeur))) {
          fautes.push(`${chemin} : « ${valeur} »`);
        }
      }
    }
    expect(fautes).toEqual([]);
  });

  it('aucune phrase affichée ne porte de jargon', () => {
    const fautes: string[] = [];
    // Les textes entre balises : >Fermer le canevas< et {'…canevas…'}
    const phrases = /(?:>([^<>{}]*[a-zà-ÿ][^<>{}]*)<|["'`]([^"'`\n]{12,})["'`])/g;
    for (const { chemin, texte } of sources) {
      for (const [, entreBalises, litteral] of texte.matchAll(phrases)) {
        const valeur = entreBalises ?? litteral ?? '';
        if (MOTS_INTERDITS.some((mot) => mot.test(valeur))) {
          fautes.push(`${chemin} : « ${valeur.trim().slice(0, 70)} »`);
        }
      }
    }
    expect(fautes).toEqual([]);
  });
});
