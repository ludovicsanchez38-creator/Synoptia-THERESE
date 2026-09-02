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
 *
 * B-235 (01/09) : la règle prétendait balayer toute l'application et était
 * indexée sur `bg-error/10`, une classe que la migration vers les jetons a
 * remplacée par `bg-[var(--color-error-tint)]`. Elle restait donc verte
 * pendant que la dérive revenait par la porte d'à côté : deux bandeaux muets
 * de plus, invisibles pour elle. Second aveuglement, dans l'autre sens : le
 * rôle était cherché sur la SEULE ligne du fond, alors qu'une balise écrite
 * sur plusieurs lignes porte son `role="alert"` en dessous. On lit désormais
 * la balise ouvrante entière, sinon la règle accuse un bandeau qui annonce.
 *
 * B-201 (02/09) : troisième aveuglement, et le plus large. La règle exigeait
 * un FOND teinté avant de regarder quoi que ce soit : elle couvrait la forme
 * visuelle « bandeau », pas la catégorie « message d'erreur ». Un refus rendu
 * en simple texte rouge - « La clé API doit commencer par "sk-ant-" », dans
 * `LLMTab`, huit lignes au-dessus d'un succès qui, lui, porte `role="status"`
 * - n'était jamais scanné : l'échec muet, la réussite annoncée, exactement
 * l'asymétrie que 0.49 voulait fermer. Le balayage part désormais de la
 * CONDITION et lit la première balise ouvrante qu'elle rend, quel que soit
 * son habillage. Une balise auto-fermante est ignorée : une icône ne porte
 * pas de message, et lui coller `role="alert"` annoncerait du vide.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

const RACINE = path.join(__dirname, '..');
const CONDITION = /\{\s*(error|erreur|\w*Error)\s*&&\s*\(?/;
const FOND_ERREUR = /bg-error\/10|bg-red-500\/10|color-error-tint/;
const ANNONCE = /role="alert"|aria-live=/;

function fichiersSources(dossier: string): string[] {
  return readdirSync(dossier).flatMap((entree) => {
    const complet = path.join(dossier, entree);
    if (statSync(complet).isDirectory()) return fichiersSources(complet);
    if (!entree.endsWith('.tsx')) return [];
    if (entree.includes('.test.') || entree.includes(' 2.')) return [];
    return [complet];
  });
}

/** La balise ouvrante qui porte le fond d'erreur, du `<` jusqu'à son `>`. */
function baliseOuvrante(lignes: string[], j: number): string {
  let debut = j;
  while (debut > 0 && j - debut < 4 && !/<[A-Za-z]/.test(lignes[debut])) debut -= 1;
  let fin = j;
  while (fin < lignes.length - 1 && fin - j < 8 && !/>\s*$/.test(lignes[fin])) fin += 1;
  return lignes.slice(debut, fin + 1).join('\n');
}

/** Marqueurs qui font d'un élément un message d'erreur, fond teinté ou non. */
const MARQUEUR_ERREUR = /bg-error\/10|bg-red-500\/10|color-error-tint|text-error|text-red-[0-9]/;

/**
 * La première balise ouvrante rendue par la condition de la ligne `i`,
 * du `<` jusqu'à son `>`, ou `null` si on n'en trouve pas.
 */
function premiereBaliseRendue(lignes: string[], i: number): string | null {
  const bloc = lignes.slice(i, i + 12).join('\n');
  const condition = bloc.match(CONDITION);
  if (!condition) return null;
  const apres = bloc.slice(bloc.search(CONDITION) + condition[0].length);
  const debut = apres.search(/<[A-Za-z]/);
  if (debut < 0) return null;
  const depuis = apres.slice(debut);
  let profondeur = 0;
  for (let k = 0; k < depuis.length; k += 1) {
    const caractere = depuis[k];
    if (caractere === '{') profondeur += 1;
    else if (caractere === '}') profondeur -= 1;
    else if (caractere === '>' && profondeur === 0) return depuis.slice(0, k + 1);
  }
  return null;
}

/** Les messages d'erreur muets sans fond teinté, en « chemin:ligne ». */
function messagesMuets(): string[] {
  const muets: string[] = [];
  for (const fichier of fichiersSources(path.join(RACINE, 'components'))) {
    const lignes = readFileSync(fichier, 'utf8').split('\n');
    lignes.forEach((ligne, i) => {
      if (!CONDITION.test(ligne)) return;
      const balise = premiereBaliseRendue(lignes, i);
      // Auto-fermante = une icône, pas un message : rien à annoncer.
      if (!balise || balise.trimEnd().endsWith('/>')) return;
      if (!MARQUEUR_ERREUR.test(balise)) return;
      if (!ANNONCE.test(balise)) muets.push(`${path.relative(RACINE, fichier)}:${i + 1}`);
    });
  }
  return muets;
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
        if (!ANNONCE.test(baliseOuvrante(lignes, j))) {
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

  it('un message d’erreur sans fond teinté est annoncé lui aussi', () => {
    expect(messagesMuets()).toEqual([]);
  });

  it('la règle trouve bien des bandeaux à surveiller (sinon elle ne prouve rien)', () => {
    const annonces = fichiersSources(path.join(RACINE, 'components')).filter((f) =>
      /role="alert"/.test(readFileSync(f, 'utf8')),
    );
    expect(annonces.length).toBeGreaterThan(10);
  });
});
