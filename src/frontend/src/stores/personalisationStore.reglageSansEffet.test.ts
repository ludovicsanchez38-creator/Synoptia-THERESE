/**
 * B-095 : un réglage déclaré qui n'a aucun lecteur.
 *
 * `showGuidedPrompts` gouvernait l'affichage des invites guidées. La surface
 * qu'il commandait a été retirée avec `GuidedPrompts` (B-094) ; le réglage,
 * lui, est resté dans le magasin et dans le type de l'API. Il compilait, il
 * passait le lint, il se relisait à chaque refactor, et il ne commandait plus
 * rien : un interrupteur dont le fil a été coupé.
 *
 * La règle testée n'est pas « ce champ ne doit pas exister ». C'est
 * « déclaré ⇒ lu ». Le jour où quelqu'un rebranche de vraies invites guidées
 * et remet le réglage EN LE LISANT quelque part, ce test reste vert. Il ne
 * rougit que sur le cas qui a produit la fiche : un réglage sans lecteur.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';

const ici = dirname(fileURLToPath(import.meta.url));
const racineSrc = resolve(ici, '..');
const MAGASIN = join(racineSrc, 'stores/personalisationStore.ts');
const API = join(racineSrc, 'services/api/personalisation.ts');

function fichiers(dossier: string, acc: string[] = []): string[] {
  for (const entree of readdirSync(dossier)) {
    if (entree === 'node_modules' || entree === 'dist') continue;
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) {
      fichiers(chemin, acc);
      continue;
    }
    if (!/\.(tsx|ts)$/.test(entree)) continue;
    acc.push(chemin);
  }
  return acc;
}

function estUnTest(chemin: string): boolean {
  return /\.(test|spec)\.(tsx|ts)$/.test(chemin);
}

const tousLesFichiers = fichiers(racineSrc);

/**
 * Le champ est-il DÉCLARÉ dans ce fichier ? On cherche une position de
 * déclaration (`cle:` ou `cle?:` en début de ligne), pas une mention : sans
 * cela, le commentaire qui explique le retrait suffirait à faire croire que
 * le réglage est revenu.
 */
function declare(source: string, cle: string): boolean {
  return new RegExp(`^\\s*${cle}\\s*\\??\\s*:`, 'm').test(source);
}

/** Les fichiers de production qui mentionnent `cle`, hors le sien propre. */
function lecteurs(cle: string, declaration: string): string[] {
  return tousLesFichiers.filter(
    (chemin) =>
      chemin !== declaration &&
      !estUnTest(chemin) &&
      readFileSync(chemin, 'utf8').includes(cle),
  );
}

describe('B-095 - un réglage déclaré est un réglage lu', () => {
  it('le balayage a bien vu le magasin et le module d’API', () => {
    // Témoin de non-vacuité : sans lui, un chemin devenu faux rendrait une
    // liste vide, et « aucun réglage orphelin » serait vrai sans rien lire.
    expect(tousLesFichiers.length).toBeGreaterThan(200);
    expect(tousLesFichiers).toContain(MAGASIN);
    expect(tousLesFichiers).toContain(API);
  });

  it('le réglage d’affichage des invites guidées ne survit pas à sa surface', () => {
    const declareDansLeMagasin = declare(readFileSync(MAGASIN, 'utf8'), 'showGuidedPrompts');
    const orphelin =
      declareDansLeMagasin && lecteurs('showGuidedPrompts', MAGASIN).length === 0;

    expect(
      orphelin,
      'personalisationStore déclare showGuidedPrompts et aucun fichier de production ne le lit',
    ).toBe(false);
  });

  it('son miroir dans le type d’API ne survit pas davantage', () => {
    const declareDansLApi = declare(readFileSync(API, 'utf8'), 'show_guided_prompts');
    const orphelin =
      declareDansLApi && lecteurs('show_guided_prompts', API).length === 0;

    expect(
      orphelin,
      'services/api/personalisation déclare show_guided_prompts et personne ne le lit',
    ).toBe(false);
  });
});
